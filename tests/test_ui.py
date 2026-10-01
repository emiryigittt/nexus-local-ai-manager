import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from backend.memory import MemoryRepository  # noqa: E402
from frontend.app import SpotlightApp  # noqa: E402
from frontend.memory_dialog import MemoryDialog  # noqa: E402


def test_spotlight_interface_has_primary_workflows():
    app = QApplication.instance() or QApplication([])
    window = SpotlightApp()

    assert window.windowTitle() == "Nexus"
    assert len(window.shortcuts) == 10
    assert window.input_line.isEnabled()
    assert window.input_line.accessibleName() == "Nexus komut alanı"
    assert window.notch_button.isVisibleTo(window)
    assert not window.dock_overview.isVisibleTo(window)
    assert not window.composer.isVisibleTo(window)
    assert not window.chat_content.isVisibleTo(window)
    assert window.local_badge.text() == "YEREL MODEL"

    window.toggle_private_session()
    assert window.private_session is True
    assert window.local_badge.text() == "ÖZEL OTURUM"
    assert window.local_badge.property("mode") == "private"

    window.close()
    app.processEvents()


def test_memory_manager_lists_and_filters_local_memories(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = MemoryRepository(tmp_path / "ui-memory.db")
    repository.add("Kısa yanıtları tercih eder", "preference")
    dialog = MemoryDialog(repository)

    assert dialog.list.count() == 1
    assert "1 kayıt" in dialog.counts.text()
    dialog.search.setText("bulunmayan")
    assert dialog.list.count() == 0

    dialog.close()
    app.processEvents()
