import pandas as pd
from utils import clean_account_value, log_step
from typing import Tuple, Dict


@log_step
def load_and_clean(file_path: str, required_columns: list) -> pd.DataFrame:

    df = pd.read_excel(file_path, engine='xlrd')
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing required columns: {missing_cols}")
        return pd.DataFrame()

    df['Account'] = df['Account'].apply(clean_account_value)
    df = df[df['Account'].notna() & (df['Account'] != '') & (df['Account'] != 'nan')]
    df['Document Date'] = pd.to_datetime(df['Document Date'], errors='coerce').dt.date
    df = df.dropna(subset=['Document Date'])
    return df


@log_step
def summarize_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:

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
