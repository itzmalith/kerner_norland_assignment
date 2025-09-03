import sys
import logging
from src.config import INPUT_FILE, OUTPUT_FILE, REQUIRED_COLUMNS
from src.processing import load_and_clean, summarize_data
from src.report_writer import write_report


def main():
    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info("----- Starting Report Automation ----")

    # Load and clean data
    df = load_and_clean(INPUT_FILE, REQUIRED_COLUMNS)
    if df is None or df.empty:
        logging.critical("Failed to load valid data. Exiting...")
        sys.exit(1)

    # Process data
    summary_df, account_data_dict = summarize_data(df)

    # Write report
    success = write_report(summary_df, account_data_dict, OUTPUT_FILE)
    if success:
        logging.info(f"Report saved at '{OUTPUT_FILE}'")
    else:
        logging.critical("Failed to write the report. Exiting...")
        sys.exit(1)

    logging.info("----- Report Automation Finished Successfully ----")


if __name__ == "__main__":
    main()
