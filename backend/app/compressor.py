from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


MIN_QUALITY = 1
MAX_QUALITY = 95


class InvalidImageError(Exception):
    """Raised when uploaded bytes are not a valid JPEG image."""


class TargetSizeUnreachableError(Exception):
    """Raised when JPEG quality alone cannot reach the requested size."""


def _open_jpeg(image_bytes: bytes) -> Image.Image:
    try:
        with Image.open(BytesIO(image_bytes)) as uploaded_image:
            if uploaded_image.format != "JPEG":
                raise InvalidImageError("JPEG 파일만 업로드할 수 있습니다.")

            uploaded_image.load()
            corrected_image = ImageOps.exif_transpose(uploaded_image)

            if corrected_image.mode != "RGB":
                corrected_image = corrected_image.convert("RGB")
            else:
                corrected_image = corrected_image.copy()

            return corrected_image
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise InvalidImageError("손상되었거나 유효하지 않은 JPEG 파일입니다.") from error


def _encode_jpeg(image: Image.Image, quality: int) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def compress_jpeg(image_bytes: bytes, target_size_bytes: int) -> bytes:
    image = _open_jpeg(image_bytes)

    if len(image_bytes) <= target_size_bytes:
        return image_bytes

    lowest_quality_bytes = _encode_jpeg(image, MIN_QUALITY)
    if len(lowest_quality_bytes) > target_size_bytes:
        raise TargetSizeUnreachableError(
            "해상도를 변경하지 않고는 목표 용량 이하로 압축할 수 없습니다."
        )

    best_bytes = lowest_quality_bytes
    low = MIN_QUALITY + 1
    high = MAX_QUALITY

    while low <= high:
        quality = (low + high) // 2
        candidate_bytes = _encode_jpeg(image, quality)

        if len(candidate_bytes) <= target_size_bytes:
            best_bytes = candidate_bytes
            low = quality + 1
        else:
            high = quality - 1

    return best_bytes
