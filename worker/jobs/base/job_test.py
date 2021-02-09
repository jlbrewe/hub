from unittest import mock

import pytest
from celery.exceptions import Ignore

from .job import DEBUG, ERROR, INFO, WARN, Job


def test_logging():
    """On each log entry send_event is called with the log."""
    job = Job()
    job.begin(task_id=4321)

    current = {}

    def send_event(self, event, **kwargs):
        assert event == "task-updated"
        current["state"] = kwargs.get("state")
        current["log"] = kwargs.get("log")

    with mock.patch(
        "celery.Task.send_event", new=send_event,
    ):

        for index, level in enumerate(["error", "warn", "info", "debug"]):
            getattr(job, level)("{} message".format(level))

            log = job.log_entries[-1]
            assert "time" in log
            assert log["level"] == index
            assert log["message"] == "{} message".format(level)
            assert current["state"] == "RUNNING"
            assert current["log"] == job.log_entries


def test_success():
    """Returns both result and log."""
    job = Job()
    job.begin()
    returns = job.success(42)
    assert returns["result"] == 42
    assert returns["log"] == []


def test_terminated():
    """Calls flush"""
    job = Job()
    job.begin()
    job.terminated()


def test_do_unimplemented():
    """Derived classes must implement do()."""
    job = Job()
    with pytest.raises(NotImplementedError) as excinfo:
        job.do()
    assert "Method do() is not implemented" in str(excinfo.value)
