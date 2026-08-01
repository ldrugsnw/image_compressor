from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .compressor import (
    FormatConversionRequiredError,
    InvalidImageError,
    ResizeRequiredError,
    TargetSizeUnreachableError,
    compress_to_jpeg,
)


MAX_UPLOAD_SIZE_BYTES = 10_000_000


app = FastAPI(title="Image Compressor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://didactic-potato-7v7wxxqvgx5p347w-5173.app.github.dev",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"message": "Image Compressor API is running."}


def _download_filename(original_filename: str | None) -> str:
    safe_name = Path(original_filename or "image.jpg").name
    stem = Path(safe_name).stem or "image"
    ascii_stem = "".join(
        character
        for character in stem
        if character.isascii() and (character.isalnum() or character in ("-", "_"))
    )
    return f"{ascii_stem or 'image'}_compressed.jpg"


@app.post("/images/compress")
async def compress_image(
    file: UploadFile = File(...),
    target_size_kb: int = Form(...),
    allow_resize: bool = Form(False),
    allow_format_conversion: bool = Form(False),
) -> Response:
    if target_size_kb <= 0:
        raise HTTPException(
            status_code=400,
            detail="목표 용량은 0보다 큰 정수여야 합니다.",
        )

    image_bytes = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="업로드한 파일이 비어 있습니다.")
    if len(image_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="파일 용량은 10 MB 이하여야 합니다.",
        )

    try:
        compressed_bytes = compress_to_jpeg(
            image_bytes=image_bytes,
            target_size_bytes=target_size_kb * 1000,
            allow_resize=allow_resize,
            allow_format_conversion=allow_format_conversion,
        )
    except FormatConversionRequiredError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "format_conversion_required",
                "message": str(error),
                "original_format": error.original_format,
                "result_format": "JPEG",
            },
        ) from error
    except ResizeRequiredError as error:
        original_width, original_height = error.original_size
        suggested_width, suggested_height = error.suggested_size
        raise HTTPException(
            status_code=409,
            detail={
                "code": "resize_required",
                "message": str(error),
                "original_width": original_width,
                "original_height": original_height,
                "suggested_width": suggested_width,
                "suggested_height": suggested_height,
            },
        ) from error
    except (InvalidImageError, TargetSizeUnreachableError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    filename = _download_filename(file.filename)
    return Response(
        content=compressed_bytes,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
