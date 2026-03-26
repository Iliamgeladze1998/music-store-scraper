import pytest
from unittest import mock
import sys
import os
import pandas as pd

import master_app

@mock.patch('gspread.authorize')
def test_upload_to_google_sheets_mocked(mock_gspread):
    # Mock Google Sheets API
    mock_client = mock.Mock()
    mock_sheet = mock.Mock()
    mock_client.open_by_key.return_value.sheet1 = mock_sheet
    mock_gspread.return_value = mock_client
    # Create a dummy file
    test_file = 'test.xlsx'
    df = pd.DataFrame({'a': [1, 2]})
    df.to_excel(test_file, index=False)
    result = master_app.upload_to_google_sheets(test_file)
    os.remove(test_file)
    assert result is True

@mock.patch('smtplib.SMTP')
@mock.patch('subprocess.run')
def test_run_script_handles_error(mock_run, mock_smtp):
    mock_run.side_effect = Exception('fail')
    result = master_app.run_script('fake.py', max_retries=0)
    assert result is False

def test_find_latest_report_empty():
    # Should return None if no files
    with mock.patch('glob.glob', return_value=[]):
        assert master_app.find_latest_report() is None
