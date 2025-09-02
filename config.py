from pathlib import Path

# Input and output file paths
BASE_DIR = Path(
    "/Users/malithlekamge/Developer/Automation Engineer/kerner_norland_assignment/python_automation_assignment/sheets")
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
