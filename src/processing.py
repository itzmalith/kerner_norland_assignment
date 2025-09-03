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
    df['Document Date'] = pd.to_datetime(df['Document Date'], errors='coerce').dt.date
    df = df.dropna(subset=['Document Date'])
    return df


@handle_exceptions
@log_step
def summarize_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    '''
        Summarizes data by grouping and splitting by account:

        :param df: Cleaned DataFrame with required columns.
        :return: Tuple of (summary DataFrame, dict of account DataFrames).
    '''
    summary_df = df.groupby(
        ['Comapany', 'Account', 'Document currency', 'Local Currency']
    )[['Amount in doc. curr.', 'Amount in local currency']].sum().reset_index()

    accounts = df['Account'].unique()
    account_data_dict = {acc: df[df['Account'] == acc].copy() for acc in accounts}

    # Drop 'Entry Date' if exists
    for acc_df in account_data_dict.values():
        if 'Entry Date' in acc_df.columns:
            acc_df.drop(columns=['Entry Date'], inplace=True)

    return summary_df, account_data_dict