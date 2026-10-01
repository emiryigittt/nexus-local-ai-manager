"""Cancellable setup jobs; never block the UI or leave a child on dismissal."""

import json
import tempfile
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, pyqtSignal

from backend.app_paths import ensure_data_dirs
from backend.runtime import resource_root, task_command


class SetupTask(QObject):
    event_received = pyqtSignal(dict)
    completed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.process.readyReadStandardOutput.connect(lambda: self.process.readAllStandardOutput())
        self.process.readyReadStandardError.connect(lambda: self.process.readAllStandardError())
        self.poll = QTimer(self)
        self.poll.setInterval(100)
        self.poll.timeout.connect(self.read_events)
        self.deadline = QTimer(self)
        self.deadline.setSingleShot(True)
        self.deadline.timeout.connect(self._timeout)
        self.path = None
        self.offset = 0
        self.buffer = b""
        self.last_stage = ""
        self.cancelled = False

    @property
    def busy(self):
        return self.process.state() != QProcess.ProcessState.NotRunning

    def start(self, task, script, arguments=(), timeout=45000):
        if self.busy:
            return
        self._cleanup()
        cache = ensure_data_dirs() / "cache"
        with tempfile.NamedTemporaryFile(dir=cache, prefix="setup-", suffix=".jsonl", delete=False) as stream:
            self.path = Path(stream.name)
        self.offset = 0
        self.buffer = b""
        self.last_stage = ""
        self.cancelled = False
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("NEXUS_SETUP_EVENTS", str(self.path))
        self.process.setProcessEnvironment(environment)
        command = task_command(task, script, arguments)
        self.process.setProgram(command[0])
        self.process.setArguments(command[1:])
        self.process.setWorkingDirectory(str(resource_root()))
        self.poll.start()
        self.deadline.start(timeout)
        self.process.start()

    def read_events(self):
        if not self.path or not self.path.exists():
            return
        with self.path.open("rb") as stream:
            stream.seek(self.offset)
            chunk = stream.read(65536)
            self.offset += len(chunk)
        self.buffer += chunk
        lines = self.buffer.split(b"\n")
        self.buffer = lines[-1][-16384:]
        for line in lines[:-1]:
            try:
                value = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(value, dict) and not self.cancelled:
                self.last_stage = value.get("stage", "")
                self.event_received.emit(value)

    def _finished(self, code, status):
        self.read_events()
        success = not self.cancelled and code == 0 and status == QProcess.ExitStatus.NormalExit and self.last_stage == "ready"
        self._cleanup()
        self.completed.emit(success)

    def _error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._cleanup()
            self.completed.emit(False)

    def _timeout(self):
        self.stop()

    def stop(self):
        self.cancelled = True
        if self.busy:
            self.process.kill()
            self.process.waitForFinished(1000)
        self._cleanup()
        return not self.busy

    def _cleanup(self):
        self.poll.stop()
        self.deadline.stop()
        if self.path:
            self.path.unlink(missing_ok=True)
            self.path = None
