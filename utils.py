import functools
from datetime import datetime
import pandas as pd
from typing import Any, Optional


def log_step(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[INFO] Starting '{func.__name__}'...")
        result = func(*args, **kwargs)
        print(f"[INFO] Finished '{func.__name__}'")
        return result

    return wrapper


def handle_exceptions(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR] Exception in {func.__name__}: {e}")
            return None

    return wrapper


# --data cleaning
def clean_account_value(x: Any) -> Optional[str]:

    if pd.isna(x):
        return None
    try:
        if isinstance(x, float) and x.is_integer():
            return str(int(x))
        return str(x).strip()
    except Exception:
        return str(x).strip()


def validate_columns(df: pd.DataFrame, required_columns: list) -> bool:

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(f"[ERROR] Missing required columns: {missing}")
        return False
    return True


def current_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")
