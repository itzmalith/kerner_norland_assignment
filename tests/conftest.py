# tests/conftest.py
import pytest
import pandas as pd
from datetime import date

@pytest.fixture
def raw_data_dict() -> dict:
    """Provides the raw data from the user as a dictionary."""
    return {
        'Comapany': ['UN0100', 'UN0100', 'XT0150', 'UN0150'],
        'Account': [63010001.0, 63010001.0, 63010012.0, 63010502.0],
        'Document Date': ['2020-06-01', '2020-06-02', '2020-06-30', '2020-06-10'],
        'Document currency': ['USD', 'USD', 'LKR', 'LKR'],
        'Local Currency': ['USD', 'USD', 'USD', 'USD'],
        'Amount in doc. curr.': [-1000.0, 500.0, 20000.0, 5000.0],
        'Amount in local currency': [-1000.0, 500.0, 110.0, 27.0],
        'Entry Date': ['2020-06-02', '2020-06-03', '2020-07-01', '2020-06-11'],
        'Text': ['Text 1', 'Text 2', 'Text 3', 'Text 4']
    }

@pytest.fixture
def sample_dataframe(raw_data_dict) -> pd.DataFrame:
    """Provides a cleaned DataFrame based on the user's data for use in tests."""
    df = pd.DataFrame(raw_data_dict)
    # Perform the same cleaning steps as in the application
    df['Account'] = df['Account'].apply(lambda x: str(int(x)) if pd.notna(x) and isinstance(x, float) and x.is_integer() else str(x))
    df['Document Date'] = pd.to_datetime(df['Document Date']).dt.date
    return df