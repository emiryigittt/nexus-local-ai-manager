"""Tests must never open the user's live Nexus database or preferences."""

import os
import tempfile

import pytest

_test_data = tempfile.TemporaryDirectory(prefix="nexus-tests-")
os.environ["NEXUS_DATA_DIR"] = _test_data.name
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session", autouse=True)
def qt_application():
    """Keep one QApplication alive while any test-owned Qt objects can exist."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    yield app
    app.processEvents()
