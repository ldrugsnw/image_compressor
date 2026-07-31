from io import BytesIO

from PIL import Image

from app.compressor import compress_jpeg


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
