import base64

from PyQt6.QtGui import QImage

from frontend.image_utils import qimage_to_base64_adaptive


def test_image_conversion_produces_jpeg_and_scales():
    image = QImage(2_000, 1_000, QImage.Format.Format_RGB32)
    image.fill(0x336699)

    encoded = qimage_to_base64_adaptive(image, max_dim=1_024)
    raw = base64.b64decode(encoded)
    converted = QImage.fromData(raw, "JPEG")

    assert raw.startswith(b"\xff\xd8")
    assert converted.width() == 1_024
    assert converted.height() == 512


def test_null_image_returns_none():
    assert qimage_to_base64_adaptive(QImage()) is None
