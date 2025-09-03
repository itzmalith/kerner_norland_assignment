import pandas as pd
from pandas.testing import assert_frame_equal
from src.processing import load_and_clean, summarize_data
from src.config import REQUIRED_COLUMNS


def test_load_and_clean_with_new_data(mocker, raw_data_dict):
    """Test load_and_clean with the user's specific dataset."""
    raw_df = pd.DataFrame(raw_data_dict)
    mocker.patch('pandas.read_excel', return_value=raw_df)

    cleaned_df = load_and_clean("dummy/path.xls", REQUIRED_COLUMNS)

    assert len(cleaned_df) == 4
    assert cleaned_df['Account'].tolist() == ['63010001', '63010001', '63010012', '63010502']
    assert all(col in cleaned_df.columns for col in REQUIRED_COLUMNS)


def test_summarize_data_with_new_data(sample_dataframe):
    """Test data summarization with the user's specific dataset."""
    summary_df, account_dict = summarize_data(sample_dataframe)

    # Expected summary
    expected_summary_data = {
        'Comapany': ['UN0100', 'UN0150', 'XT0150'],
        'Account': ['63010001', '63010502', '63010012'],
        'Document currency': ['USD', 'LKR', 'LKR'],
        'Amount in doc. curr.': [-500.0, 5000.0, 20000.0],
        'Local Currency': ['USD', 'USD', 'USD'],
        'Amount in local currency': [-500.0, 27.0, 110.0]
    }

    # Ensure column order matches the actual summarize_data output
    expected_summary_df = pd.DataFrame(expected_summary_data)[
        ['Comapany', 'Account', 'Document currency', 'Amount in doc. curr.',
         'Local Currency', 'Amount in local currency']
    ]

    # Sort both dataframes by 'Account' to ensure consistent comparison
    summary_df = summary_df.sort_values(by='Account').reset_index(drop=True)
    expected_summary_df = expected_summary_df.sort_values(by='Account').reset_index(drop=True)

    # Compare DataFrames
    assert_frame_equal(summary_df, expected_summary_df)

    # Test account dictionary
    assert set(account_dict.keys()) == {'63010001', '63010012', '63010502'}
    assert len(account_dict['63010001']) == 2
    assert 'Entry Date' not in account_dict['63010001'].columns
