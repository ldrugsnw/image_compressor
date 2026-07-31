from io import BytesIO

import pytest
from PIL import Image

from app.compressor import ResizeRequiredError, compress_jpeg


def create_test_jpeg() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (100, 100), color="red")
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def test_returns_original_jpeg_when_already_under_target() -> None:
    original_bytes = create_test_jpeg()

    compressed_bytes = compress_jpeg(
        image_bytes=original_bytes,
        target_size_bytes=len(original_bytes),
    )

    assert compressed_bytes == original_bytes


def test_compresses_jpeg_below_target_size() -> None:
    original_bytes = create_test_jpeg()
    target_size_bytes = len(original_bytes) - 1

    compressed_bytes = compress_jpeg(
        image_bytes=original_bytes,
        target_size_bytes=target_size_bytes,
    )

    assert len(compressed_bytes) <= target_size_bytes
    assert len(compressed_bytes) < len(original_bytes)

    with Image.open(BytesIO(compressed_bytes)) as compressed_image:
        assert compressed_image.format == "JPEG"


def test_suggests_smaller_dimensions_when_resize_is_required() -> None:
    original_bytes = create_test_jpeg()

    with pytest.raises(ResizeRequiredError) as caught_error:
        compress_jpeg(
            image_bytes=original_bytes,
            target_size_bytes=300,
        )

    assert caught_error.value.original_size == (100, 100)
    suggested_width, suggested_height = caught_error.value.suggested_size
    assert suggested_width < 100
    assert suggested_height < 100
    assert suggested_width == suggested_height


def test_resizes_jpeg_after_user_approval() -> None:
    original_bytes = create_test_jpeg()
    target_size_bytes = 300

    compressed_bytes = compress_jpeg(
        image_bytes=original_bytes,
        target_size_bytes=target_size_bytes,
        allow_resize=True,
    )

    assert len(compressed_bytes) <= target_size_bytes

    with Image.open(BytesIO(compressed_bytes)) as compressed_image:
        assert compressed_image.width < 100
        assert compressed_image.height < 100
