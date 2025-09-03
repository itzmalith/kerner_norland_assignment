import pandas as pd
from src.utils import clean_account_value, log_step, handle_exceptions
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


@handle_exceptions
@log_step
def load_and_clean(file_path: str, required_columns: list) -> pd.DataFrame:
    '''
        Loads an Excel file and cleans its data:

        :param file_path: Path to input Excel file.
        :param required_columns: List of columns expected in the file.
        :return: Cleaned DataFrame or empty DataFrame if invalid.
    '''
    try:
        df = pd.read_excel(file_path, engine='xlrd')
    except FileNotFoundError:
        logger.error(f"Input file not found at: {file_path}")
        return pd.DataFrame()

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return pd.DataFrame()

    df['Account'] = df['Account'].apply(clean_account_value)

    df = df[df['Account'].notna() & (df['Account'] != '') & (df['Account'] != 'nan')]

    df['Document Date'] = pd.to_datetime(df['Document Date'], errors='coerce', dayfirst=True).dt.date

    # Check for accounts with invalid dates
    accounts_with_all_invalid_dates = df.groupby('Account')['Document Date'].apply(lambda x: x.isna().all())
    accounts_all_invalid = accounts_with_all_invalid_dates[accounts_with_all_invalid_dates].index.tolist()

    if accounts_all_invalid:
        print(f"Found {len(accounts_all_invalid)} accounts with ALL invalid dates: {accounts_all_invalid}")

        valid_dates = df[df['Document Date'].notna()]['Document Date']
        if len(valid_dates) > 0:
            median_date = pd.to_datetime(valid_dates).median().date()
            print(f"Setting median date ({median_date}) for accounts with invalid dates...")
            mask = df['Account'].isin(accounts_all_invalid) & df['Document Date'].isna()
            df.loc[mask, 'Document Date'] = median_date

    df = df.dropna(subset=['Document Date'])

    return df


@handle_exceptions
@log_step
def summarize_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Summarizes data by grouping and splitting by account.

    :param df: Cleaned DataFrame with required columns.
    :return: Tuple of (summary DataFrame, dict of account DataFrames).
    """
    # Define the aggregation rules for each column
    agg_rules = {
        'Amount in doc. curr.': 'sum',
        'Amount in local currency': 'sum',
        'Comapany': 'first',
        'Document currency': 'first',
        'Local Currency': 'first'
    }

    summary_df = df.groupby('Account').agg(agg_rules).reset_index()

    column_order = [
        'Comapany',
        'Account',
        'Document currency',
        'Amount in doc. curr.',
        'Local Currency',
        'Amount in local currency'
    ]
    summary_df = summary_df[column_order]

    accounts = df['Account'].unique()
    account_data_dict = {acc: df[df['Account'] == acc].copy() for acc in accounts}

    for acc in account_data_dict:
        if 'Entry Date' in account_data_dict[acc].columns:
            account_data_dict[acc] = account_data_dict[acc].drop(columns=['Entry Date'])

    return summary_df, account_data_dict
