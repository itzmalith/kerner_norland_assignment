import sys
from config import INPUT_FILE, OUTPUT_FILE, REQUIRED_COLUMNS
from processing import load_and_clean, summarize_data
from report_writer import write_report


def main():
    print("----- Starting Report Automation ----")

    # Load and clean data
    df = load_and_clean(INPUT_FILE, REQUIRED_COLUMNS)
    if df is None or df.empty:
        print("[CRITICAL] Failed to load valid data. Exiting...")
        sys.exit(1)

    # Process data
    summary_df, account_data_dict = summarize_data(df)

    # Write report
    success = write_report(summary_df, account_data_dict, OUTPUT_FILE)
    if success:
        print(f"[SUCCESS] Report saved at '{OUTPUT_FILE}'")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
