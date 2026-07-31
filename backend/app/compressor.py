from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


MIN_QUALITY = 60
MAX_QUALITY = 95


class InvalidImageError(Exception):
    """Raised when uploaded bytes are not a valid JPEG image."""


class TargetSizeUnreachableError(Exception):
    """Raised when the target cannot be reached even after resizing."""


class ResizeRequiredError(Exception):
    """Raised when reaching the target requires smaller image dimensions."""

    def __init__(
        self,
        original_size: tuple[int, int],
        suggested_size: tuple[int, int],
    ) -> None:
        super().__init__("목표 용량을 맞추려면 이미지 해상도를 줄여야 합니다.")
        self.original_size = original_size
        self.suggested_size = suggested_size


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


def _suggest_resize(image: Image.Image, target_size_bytes: int) -> tuple[int, int]:
    width, height = image.size

    while width > 1 or height > 1:
        width = max(1, int(width * 0.9))
        height = max(1, int(height * 0.9))
        resized_image = image.resize((width, height), Image.Resampling.LANCZOS)

        if len(_encode_jpeg(resized_image, MIN_QUALITY)) <= target_size_bytes:
            return width, height

    raise TargetSizeUnreachableError("목표 용량이 너무 작아 압축할 수 없습니다.")


def compress_jpeg(
    image_bytes: bytes,
    target_size_bytes: int,
    allow_resize: bool = False,
) -> bytes:
    image = _open_jpeg(image_bytes)

    if len(image_bytes) <= target_size_bytes:
        return image_bytes

    lowest_quality_bytes = _encode_jpeg(image, MIN_QUALITY)
    if len(lowest_quality_bytes) > target_size_bytes:
        suggested_size = _suggest_resize(image, target_size_bytes)

        if not allow_resize:
            raise ResizeRequiredError(
                original_size=image.size,
                suggested_size=suggested_size,
            )

        image = image.resize(suggested_size, Image.Resampling.LANCZOS)
        lowest_quality_bytes = _encode_jpeg(image, MIN_QUALITY)

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
