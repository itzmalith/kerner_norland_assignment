from pathlib import Path

# Input and output file paths
BASE_DIR = Path(
    "files")
INPUT_FILE = BASE_DIR / "export.xls"
OUTPUT_FILE = BASE_DIR / "Final_Report.xlsx"

# Required columns in input file
REQUIRED_COLUMNS = [
    'Comapany',
    'Account',
    'Document Date',
    'Document currency',
    'Local Currency',
    'Amount in doc. curr.',
    'Amount in local currency'
]
