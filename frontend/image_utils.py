"""
image_utils.py - Smart Adaptive Image Processing for Nexus Vision
Preserves 1:1 original crisp pixels for screenshots and code reading (OCR),
and adaptively scales large 2K/4K images to a 1024px ceiling with 90% quality.
"""

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PyQt6.QtGui import QImage


def qimage_to_base64_adaptive(qimg: QImage, max_dim: int = 1024, quality: int = 90) -> str:
    """
    Converts a QImage to a base64 JPEG string using smart adaptive scaling:
    - If image <= 1024px: Keeps 1:1 original pixel sharpness (ideal for code and text).
    - If image > 1024px: Smoothly downscales keeping aspect ratio.
    - Quality=90 ensures crisp font boundaries without blurry JPEG artifacts.
    """
    if qimg is None or qimg.isNull():
        return None

    w = qimg.width()
    h = qimg.height()

    # Smart Adaptive Decision:
    # Small/medium images (like error dialogs, code regions) remain 100% UNTOUCHED!
    if w > max_dim or h > max_dim:
        processed_img = qimg.scaled(
            max_dim,
            max_dim,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    else:
        processed_img = qimg

    # Ensure format compatibility for clean compression
    if processed_img.hasAlphaChannel() or processed_img.format() != QImage.Format.Format_RGB32:
        processed_img = processed_img.convertToFormat(QImage.Format.Format_RGB32)

    ba = QByteArray()
    buffer = QBuffer(ba)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    processed_img.save(buffer, "JPEG", quality)

    return ba.toBase64().data().decode('utf-8')
