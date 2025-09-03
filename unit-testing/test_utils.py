import pytest
import logging
from src.utils import log_step, handle_exceptions

def test_log_step_decorator(caplog):
    """Test the log_step decorator captures log messages."""
    @log_step
    def sample_function():
        return "done"

    with caplog.at_level(logging.INFO):
        result = sample_function()

    assert result == "done"
    assert "Starting 'sample_function'..." in caplog.text
    assert "Finished 'sample_function'." in caplog.text

def test_handle_exceptions_decorator(caplog):
    """Test the handle_exceptions decorator captures error logs."""
    @handle_exceptions
    def failing_function():
        raise ValueError("Something went wrong")

    with caplog.at_level(logging.ERROR):
        result = failing_function()

    assert result is None
    assert "Exception in failing_function: Something went wrong" in caplog.text