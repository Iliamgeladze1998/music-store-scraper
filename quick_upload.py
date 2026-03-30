import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

def quick_upload_to_google_sheets():
    """Upload RE_RUN_REPORT_NEW.xlsx to Google Sheets with timestamp."""
    
    # Configuration
    spreadsheet_id = "1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94"
    report_file = "RE_RUN_REPORT_NEW.xlsx"
    credentials_file = "credentials.json"
    
    try:
        print(f"Quick Upload: Starting upload of {report_file} to Google Sheets...")
        
        # Check if file exists
        if not os.path.exists(report_file):
            print(f"Error: {report_file} not found!")
            return False
        
        if not os.path.exists(credentials_file):
            print(f"Error: {credentials_file} not found!")
            return False
        
        # Authenticate with Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        # Read the Excel file
        print(f"Reading {report_file}...")
        df = pd.read_excel(report_file)
        
        # Handle NaN values for JSON compliance
        df = df.replace({np.nan: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        
        # Convert DataFrame to list for upload
        data_to_upload = [df.columns.values.tolist()]
        
        for _, row in df.iterrows():
            row_data = []
            for value in row:
                if pd.isna(value) or value != value:
                    row_data.append(None)
                else:
                    row_data.append(value)
            data_to_upload.append(row_data)
        
        # Reset Google Sheets formatting and clear all data
        print("Resetting Google Sheets (clearing formatting, filters, and data)...")
        
        # Clear all formatting, filters, and data from a wide range
        sheet.batch_clear(["A1:Z2000"])
        
        # Remove any active filters
        try:
            sheet.clear_basic_filter()
            print("✅ Cleared basic filters")
        except:
            print("⚠️  No filters to clear")
        
        # Complete formatting reset - remove all background colors, styles, etc.
        try:
            sheet_id = sheet._properties['sheetId']
            body = {
                "requests": [
                    {
                        "updateCells": {
                            "range": {"sheetId": sheet_id},
                            "fields": "userEnteredFormat"
                        }
                    }
                ]
            }
            sheet.spreadsheet.batch_update(body)
            print("✅ Completely reset all formatting (colors, styles, etc.)")
        except Exception as format_error:
            print(f"⚠️  Warning: Could not reset all formatting: {format_error}")
        
        # Upload data to Google Sheets starting from A1
        print("Uploading data to Google Sheets...")
        sheet.update(data_to_upload)
        
        # Add timestamp to cell K1 (more visible than L1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            sheet.update_acell('K1', f'Last Update: {timestamp}')
            print(f"✅ Timestamp added to cell K1: Last Update: {timestamp}")
        except Exception as timestamp_error:
            print(f"⚠️  Warning: Could not update timestamp: {timestamp_error}")
            print("✅ Data upload still successful!")
        
        print(f"✅ Success! Uploaded {len(df)} rows to Google Sheets")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to Google Sheets: {e}")
        return False

if __name__ == "__main__":
    print("=== Quick Upload Tool ===")
    print("This tool uploads RE_RUN_REPORT_NEW.xlsx to Google Sheets")
    print()
    
    success = quick_upload_to_google_sheets()
    
    if success:
        print("\n🎉 Quick upload completed successfully!")
    else:
        print("\n💥 Quick upload failed!")
        exit(1)
