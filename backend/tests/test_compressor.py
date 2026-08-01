from io import BytesIO

import pytest
from PIL import Image

from app.compressor import (
    FormatConversionRequiredError,
    InvalidImageError,
    ResizeRequiredError,
    compress_to_jpeg,
)


def create_test_jpeg() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (100, 100), color="red")
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def create_test_webp(mode: str = "RGB", alpha: int = 255) -> bytes:
    buffer = BytesIO()
    color = (255, 0, 0, alpha) if mode == "RGBA" else "red"
    image = Image.new(mode, (100, 100), color=color)
    image.save(buffer, format="WEBP")
    return buffer.getvalue()


def create_test_png(mode: str = "RGB", alpha: int = 255) -> bytes:
    buffer = BytesIO()
    color = (255, 0, 0, alpha) if mode == "RGBA" else "red"
    image = Image.new(mode, (100, 100), color=color)
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def create_animated_png() -> bytes:
    buffer = BytesIO()
    first_frame = Image.new("RGB", (100, 100), color="red")
    second_frame = Image.new("RGB", (100, 100), color="blue")
    first_frame.save(
        buffer,
        format="PNG",
        save_all=True,
        append_images=[second_frame],
        duration=100,
        loop=0,
    )
    return buffer.getvalue()


def create_animated_webp() -> bytes:
    buffer = BytesIO()
    first_frame = Image.new("RGB", (100, 100), color="red")
    second_frame = Image.new("RGB", (100, 100), color="blue")
    first_frame.save(
        buffer,
        format="WEBP",
        save_all=True,
        append_images=[second_frame],
        duration=100,
        loop=0,
    )
    return buffer.getvalue()


def test_returns_original_jpeg_when_already_under_target() -> None:
    original_bytes = create_test_jpeg()

    compressed_bytes = compress_to_jpeg(
        image_bytes=original_bytes,
        target_size_bytes=len(original_bytes),
    )

    assert compressed_bytes == original_bytes


def test_compresses_jpeg_below_target_size() -> None:
    original_bytes = create_test_jpeg()
    target_size_bytes = len(original_bytes) - 1

    compressed_bytes = compress_to_jpeg(
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
        compress_to_jpeg(
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

    compressed_bytes = compress_to_jpeg(
        image_bytes=original_bytes,
        target_size_bytes=target_size_bytes,
        allow_resize=True,
    )

    assert len(compressed_bytes) <= target_size_bytes

    with Image.open(BytesIO(compressed_bytes)) as compressed_image:
        assert compressed_image.width < 100
        assert compressed_image.height < 100


@pytest.mark.parametrize("mode", ["RGB", "RGBA"])
def test_converts_static_opaque_webp_to_jpeg(mode: str) -> None:
    webp_bytes = create_test_webp(mode=mode, alpha=255)

    compressed_bytes = compress_to_jpeg(
        image_bytes=webp_bytes,
        target_size_bytes=10_000,
    )

    assert len(compressed_bytes) <= 10_000
    assert compressed_bytes != webp_bytes

    with Image.open(BytesIO(compressed_bytes)) as compressed_image:
        assert compressed_image.format == "JPEG"


def test_resizes_webp_after_user_approval() -> None:
    webp_bytes = create_test_webp()
    target_size_bytes = 300

    with pytest.raises(ResizeRequiredError):
        compress_to_jpeg(
            image_bytes=webp_bytes,
            target_size_bytes=target_size_bytes,
        )

    compressed_bytes = compress_to_jpeg(
        image_bytes=webp_bytes,
        target_size_bytes=target_size_bytes,
        allow_resize=True,
    )

    assert len(compressed_bytes) <= target_size_bytes

    with Image.open(BytesIO(compressed_bytes)) as compressed_image:
        assert compressed_image.format == "JPEG"
        assert compressed_image.width < 100
        assert compressed_image.height < 100


@pytest.mark.parametrize("mode", ["RGB", "RGBA"])
def test_converts_static_opaque_png_to_jpeg(mode: str) -> None:
    png_bytes = create_test_png(mode=mode, alpha=255)

    compressed_bytes = compress_to_jpeg(
        image_bytes=png_bytes,
        target_size_bytes=10_000,
        allow_format_conversion=True,
    )

    assert len(compressed_bytes) <= 10_000
    assert compressed_bytes != png_bytes

    with Image.open(BytesIO(compressed_bytes)) as compressed_image:
        assert compressed_image.format == "JPEG"


def test_resizes_png_after_user_approval() -> None:
    png_bytes = create_test_png()
    target_size_bytes = 300

    with pytest.raises(ResizeRequiredError):
        compress_to_jpeg(
            image_bytes=png_bytes,
            target_size_bytes=target_size_bytes,
            allow_format_conversion=True,
        )

    compressed_bytes = compress_to_jpeg(
        image_bytes=png_bytes,
        target_size_bytes=target_size_bytes,
        allow_resize=True,
        allow_format_conversion=True,
    )

    assert len(compressed_bytes) <= target_size_bytes

    with Image.open(BytesIO(compressed_bytes)) as compressed_image:
        assert compressed_image.format == "JPEG"
        assert compressed_image.width < 100
        assert compressed_image.height < 100


def test_requires_approval_before_converting_png_to_jpeg() -> None:
    with pytest.raises(FormatConversionRequiredError) as caught_error:
        compress_to_jpeg(
            image_bytes=create_test_png(),
            target_size_bytes=10_000,
        )

    assert caught_error.value.original_format == "PNG"


def test_rejects_transparent_png() -> None:
    with pytest.raises(InvalidImageError, match="투명 PNG"):
        compress_to_jpeg(
            image_bytes=create_test_png(mode="RGBA", alpha=128),
            target_size_bytes=10_000,
        )


def test_rejects_animated_png() -> None:
    with pytest.raises(InvalidImageError, match="애니메이션 PNG"):
        compress_to_jpeg(
            image_bytes=create_animated_png(),
            target_size_bytes=10_000,
        )


def test_rejects_transparent_webp() -> None:
    with pytest.raises(InvalidImageError, match="투명 WebP"):
        compress_to_jpeg(
            image_bytes=create_test_webp(mode="RGBA", alpha=128),
            target_size_bytes=10_000,
        )


def test_rejects_animated_webp() -> None:
    with pytest.raises(InvalidImageError, match="애니메이션 WebP"):
        compress_to_jpeg(
            image_bytes=create_animated_webp(),
            target_size_bytes=10_000,
        )
