"""Windows job object that reaps the whole process tree of a child.

The launcher starts the API gateway, and the gateway starts MCP servers, so a
stopped launcher can leave grandchildren behind. Windows attaches every process to
the job of the process that created it, which makes a kill-on-close job the only
mechanism that also survives a hard kill: closing the last handle to the job makes
the OS terminate every member, whether the launcher exited, crashed or was killed
from Task Manager. ``subprocess.Popen.terminate()`` reaches the direct child only.

Off Windows the object is inert and every method reports failure, so callers can
treat containment as a best-effort upgrade over their existing cleanup.
"""

from __future__ import annotations

import ctypes
import os
import subprocess

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_ALL_ACCESS = 0x001FFFFF
STILL_ACTIVE = 259


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", ctypes.c_ulong),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_ulong),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_ulong),
        ("SchedulingClass", ctypes.c_ulong),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _kernel32():
    """Return the configured kernel32 handle, or None where it does not exist."""
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return None
    kernel32 = windll.kernel32
    kernel32.GetLastError.restype = ctypes.c_ulong
    kernel32.GetLastError.argtypes = []
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel32.SetInformationJobObject.restype = ctypes.c_int
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_ulong,
    ]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.GetExitCodeProcess.restype = ctypes.c_int
    kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel32.CloseHandle.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    return kernel32


def process_alive(pid: int) -> bool:
    """Report whether a process id is still running, without waiting on it."""
    kernel32 = _kernel32()
    if kernel32 is None:
        raise NotImplementedError("process_alive relies on the Windows API")
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


class ProcessJob:
    """A kill-on-close job object; an inert container on every other platform."""

    def __init__(self) -> None:
        self.handle: int | None = None
        self.reason = ""

    @property
    def active(self) -> bool:
        return self.handle is not None

    def open(self) -> bool:
        """Create the job. A False return means containment is unavailable, not fatal."""
        if os.name != "nt":
            self.reason = f"job objects are Windows-only, not {os.name}"
            return False
        kernel32 = _kernel32()
        if kernel32 is None:  # pragma: no cover - unreachable on Windows
            self.reason = "ctypes.windll is unavailable"
            return False
        handle = kernel32.CreateJobObjectW(None, "NexusSupervisorJob")
        if not handle:
            self.reason = f"CreateJobObjectW failed with error {kernel32.GetLastError()}"
            return False
        limits = _ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            self.reason = f"SetInformationJobObject failed with error {kernel32.GetLastError()}"
            kernel32.CloseHandle(handle)
            return False
        self.handle = handle
        self.reason = ""
        return True

    def assign(self, process: subprocess.Popen) -> bool:
        """Put a running child, and everything it creates later, into the job.

        Membership is decided when a process is created, so a grandchild that
        already existed before this call stays outside the job. The gateway starts
        MCP servers only after a client reaches the connect endpoint, which is
        seconds after the launcher has assigned it here.
        """
        if self.handle is None:
            return False
        kernel32 = _kernel32()
        if kernel32 is None:  # pragma: no cover - not Windows
            return False
        # Reuse the handle CreateProcess gave subprocess: it already carries the
        # rights the assignment needs. A handle opened here by pid with only
        # PROCESS_SET_QUOTA | PROCESS_TERMINATE is refused with error 5 on the
        # machine this was written on, so that path is only a fallback.
        handle = getattr(process, "_handle", None)
        borrowed = bool(handle)
        if not borrowed:
            handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, process.pid)
        if not handle:
            self.reason = (
                f"No handle available for process {process.pid}: "
                f"error {kernel32.GetLastError()}"
            )
            return False
        try:
            if not kernel32.AssignProcessToJobObject(self.handle, handle):
                self.reason = (
                    f"AssignProcessToJobObject failed for process {process.pid}: "
                    f"error {kernel32.GetLastError()}"
                )
                return False
        finally:
            if not borrowed:
                kernel32.CloseHandle(handle)
        return True

    def close(self) -> None:
        """Release the job; the OS terminates any member still running."""
        handle, self.handle = self.handle, None
        if handle is None:
            return
        kernel32 = _kernel32()
        if kernel32 is not None:  # pragma: no cover - not Windows
            kernel32.CloseHandle(handle)

