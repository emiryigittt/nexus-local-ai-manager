"""The launcher's kill-on-close job must reap a grandchild it never spawned."""

import os
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from backend.process_job import ProcessJob, process_alive

NESTED_CHILD = (
    "import subprocess, sys, time; "
    "kid = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)']); "
    "print(kid.pid, flush=True); time.sleep(120)"
)


@pytest.mark.skipif(os.name != "nt", reason="job objects are a Windows mechanism")
def test_closing_the_job_reaps_a_grandchild_that_was_never_touched():
    job = ProcessJob()
    assert job.open(), job.reason
    child = subprocess.Popen(
        [sys.executable, "-c", NESTED_CHILD], stdout=subprocess.PIPE, text=True
    )
    try:
        assert job.assign(child), job.reason
        grandchild_pid = int(child.stdout.readline())
        assert process_alive(grandchild_pid)

        job.close()  # Nothing else in this test terminates either process.

        deadline = time.monotonic() + 10
        while process_alive(grandchild_pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not process_alive(grandchild_pid)
        assert child.wait(timeout=5) is not None
    finally:
        job.close()
        child.stdout.close()


@pytest.mark.skipif(os.name != "nt", reason="job objects are a Windows mechanism")
def test_an_unopened_job_refuses_to_assign():
    job = ProcessJob()
    assert not job.active
    assert not job.assign(SimpleNamespace(pid=0))
    job.close()  # Closing a job that was never opened is harmless.


@pytest.mark.skipif(os.name == "nt", reason="only the non-Windows branch is inert")
def test_the_job_is_inert_off_windows(tmp_path):
    job = ProcessJob()
    assert not job.open()
    assert "Windows" in job.reason
    assert not job.active
