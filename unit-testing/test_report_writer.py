from unittest.mock import patch, MagicMock
from src.report_writer import write_report
from src.processing import summarize_data


@patch('src.report_writer.pd.ExcelWriter')
@patch('src.report_writer.load_workbook')
@patch('src.report_writer.pd.DataFrame.to_excel')
def test_write_report(mock_to_excel, mock_load_workbook, mock_excel_writer, sample_dataframe):
    """
    Tests the logic of write_report by mocking all file system interactions.
    """
    # 1. Setup mocks
    mock_writer_instance = MagicMock()
    mock_excel_writer.return_value.__enter__.return_value = mock_writer_instance

    # Create a mock sheet object that has the max_row attribute
    mock_sheet = MagicMock()
    mock_sheet.max_row = 10  # Give it a realistic value > 2

    mock_workbook_instance = MagicMock()
    # Configure the workbook mock to return our smart sheet mock
    mock_workbook_instance.__getitem__.return_value = mock_sheet
    mock_load_workbook.return_value = mock_workbook_instance

    # 2. Prepare data
    summary_df, account_dict = summarize_data(sample_dataframe)
    output_path = "dummy/report.xlsx"

    # 3. Call the function
    write_report(summary_df, account_dict, output_path)

    # 4. Assertions
    # Was the ExcelWriter context manager created with the right path?
    mock_excel_writer.assert_called_once_with(output_path, engine='openpyxl')

    # Was to_excel called for all our dataframes? (1 summary + 3 accounts)
    assert mock_to_excel.call_count == 4

    # Was the workbook loaded back for styling?
    mock_load_workbook.assert_called_once_with(output_path)

    # Was the final workbook saved?
    mock_workbook_instance.save.assert_called_once_with(output_path)