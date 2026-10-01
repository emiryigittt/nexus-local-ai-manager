import pytest
from PyQt6.QtWidgets import QLabel

from frontend.app import SpotlightApp
from frontend.brand import ACCENT, brand_icon, brand_pixmap, mark_pixmap, mark_source
from frontend.design import STYLE, icon


@pytest.mark.parametrize("size", [16, 24, 32, 64, 256])
def test_vector_mark_has_transparency_and_visible_pixels(size, qt_application):
    image = mark_pixmap(size).toImage()
    assert image.width() == image.height() == size
    assert image.pixelColor(0, 0).alpha() == 0
    visible = sum(image.pixelColor(x, y).alpha() > 0 for x in range(size) for y in range(size))
    assert size * size * 0.2 < visible < size * size * 0.6
    # At 16px the diagonal cut is subpixel-antialiased, not an axis-aligned hole.
    center = size // 2
    assert min(image.pixelColor(x, y).alpha() for x in (center - 1, center)
               for y in (center - 1, center)) < 64


def test_icon_has_multiple_native_sizes_and_self_contained_source(qt_application):
    sizes = {size.width() for size in brand_icon().availableSizes()}
    assert {16, 24, 32, 64, 128, 256} <= sizes
    assert b"href=" not in mark_source()
    assert not icon("logo").isNull()
    assert ACCENT in STYLE and "@accent" not in STYLE


def test_monochrome_mark_and_listening_indicator_are_distinct(qt_application):
    image = mark_pixmap(64, color="#a1aaa5").toImage()
    assert image.pixelColor(16, 40).name() == "#a1aaa5"
    active = brand_pixmap(64, active=True).toImage()
    paused = brand_pixmap(64, active=False).toImage()
    assert active != paused
    assert active.pixelColor(52, 52).name() == ACCENT
    assert paused.pixelColor(52, 52).name() == "#56615b"


def test_window_header_and_tray_use_shared_brand(qt_application):
    window = SpotlightApp()
    window.wake.timer.stop()
    try:
        assert not window.windowIcon().isNull()
        assert window.windowIcon().pixmap(32).toImage() == brand_icon().pixmap(32).toImage()
        assert window.findChild(QLabel, "brandMark").pixmap().toImage() == brand_pixmap(22, tile=False).toImage()
        window.wake._set_state("Duraklatıldı")
        paused = window.wake.tray.icon().pixmap(32).toImage()
        window.wake._set_state("Dinliyor · yerel mikrofon açık")
        assert window.wake.tray.icon().pixmap(32).toImage() != paused
        key = window.wake.tray.icon().cacheKey()
        window.wake._set_state("Dinliyor · algılama gecikti, eski çağrı atlandı")
        assert window.wake.tray.icon().cacheKey() == key
    finally:
        window.close()
        qt_application.processEvents()
