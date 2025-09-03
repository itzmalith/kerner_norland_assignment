import functools
import logging
from datetime import datetime
import pandas as pd
from typing import Any, Optional, Callable

# Get a logger instance for this module
logger = logging.getLogger(__name__)


def log_step(func: Callable) -> Callable:
    '''
    Decorator to log when a function starts and ends.

    :param func: Function to be wrapped.
    :return: Wrapped function with logging.
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Starting '{func.__name__}'...")
        result = func(*args, **kwargs)
        logger.info(f"Finished '{func.__name__}'.")
        return result
    return wrapper


def handle_exceptions(func: Callable) -> Callable:
    '''
    Decorator to catch and log exceptions in a function

    :param func:  Function to be wrapped.
    :return: Wrapped function that logs errors and returns None on exception.
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Using exc_info=True provides a full traceback in the logs
            logger.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper


# --data cleaning
def clean_account_value(x: Any) -> Optional[str]:
    '''
     Cleans and converts account values into strings.

    :param x: Input account value which is originally in float format
    :return: Cleaned string or None if value is invalid
    '''
    if pd.isna(x):
        return None
    try:
        if isinstance(x, float) and x.is_integer():
            return str(int(x))
        return str(x).strip()
    except Exception:
        return str(x).strip()


def validate_columns(df: pd.DataFrame, required_columns: list) -> bool:
    '''
    Validates if required columns are present in the DataFrame

    :param df: Input pandas DataFrame
    :param required_columns: List of column names that must exist
    :return: True if all required columns exist, False otherwise
    '''
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True


def current_date_str() -> str:
    '''
    Returns the current date as a formatted string (YYYY-MM-DD).
    :return: Current date as string.
    '''
    return datetime.now().strftime("%Y-%m-%d")