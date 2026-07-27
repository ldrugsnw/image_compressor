from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .compressor import (
    InvalidImageError,
    TargetSizeUnreachableError,
    compress_jpeg,
)


app = FastAPI(title="Image Compressor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
) -> Response:
    if target_size_kb <= 0:
        raise HTTPException(
            status_code=400,
            detail="목표 용량은 0보다 큰 정수여야 합니다.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="업로드한 파일이 비어 있습니다.")

    try:
        compressed_bytes = compress_jpeg(
            image_bytes=image_bytes,
            target_size_bytes=target_size_kb * 1024,
        )
    except (InvalidImageError, TargetSizeUnreachableError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    filename = _download_filename(file.filename)
    return Response(
        content=compressed_bytes,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
