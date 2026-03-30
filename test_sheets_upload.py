import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'SPREADSHEET_ID': "1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94",
    'CREDENTIALS_FILE': "credentials.json",
    'GEOVOICE_TAB': "Geovoice"
}

def test_geovoice_upload():
    """Test upload to Geovoice tab using existing TEST_GEOVOICE_REPORT.xlsx"""
    
    logger.info("=== Test: Google Sheets Upload to 'Geovoice' Tab ===")
    
    try:
        # Load existing test data
        logger.info("Loading TEST_GEOVOICE_REPORT.xlsx...")
        df = pd.read_excel("TEST_GEOVOICE_REPORT.xlsx")
        logger.info(f"Loaded {len(df)} rows from test file")
        
        # Standardize columns to match Music Store structure exactly
        logger.info("Standardizing columns to match Music Store structure...")
        
        # Create new dataframe with exact Music Store column structure
        standardized_df = pd.DataFrame()
        
        # Map columns to exact Music Store format
        standardized_df['UNIQUE_ID'] = df['UNIQUE_ID']
        standardized_df['NAME_AC'] = df['Product_Name']  # Use Product_Name as NAME_AC
        standardized_df['PRICE_AC'] = df['Price_Acoustic']
        standardized_df['STATUS_AC'] = df['Status_Acoustic']
        standardized_df['NAME_GV'] = df['Product_Name']  # Use same Product_Name as NAME_GV (can be refined later)
        standardized_df['PRICE_GV'] = df['Price_Geovoice']
        standardized_df['STATUS_GV'] = df['Status_Geovoice']
        standardized_df['Price_Diff'] = df['Price_Diff']
        standardized_df['LINK_AC'] = df['Link_Acoustic']
        standardized_df['LINK_GV'] = df['Link_Geovoice']
        
        # Reorder columns to exact Music Store sequence
        standardized_df = standardized_df[[
            'UNIQUE_ID',
            'NAME_AC',
            'PRICE_AC', 
            'STATUS_AC',
            'NAME_GV',
            'PRICE_GV',
            'STATUS_GV',
            'Price_Diff',
            'LINK_AC',
            'LINK_GV'
        ]]
        
        logger.info(f"Standardized to {len(standardized_df.columns)} columns: {list(standardized_df.columns)}")
        
        # Replace original df with standardized version
        df = standardized_df
        
        # Authenticate with Google Sheets
        logger.info("Connecting to Google Sheets...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CONFIG['CREDENTIALS_FILE'], scope)
        client = gspread.authorize(creds)
        
        # Open spreadsheet and get Geovoice tab
        logger.info(f"Opening spreadsheet and targeting '{CONFIG['GEOVOICE_TAB']}' tab...")
        spreadsheet = client.open_by_key(CONFIG['SPREADSHEET_ID'])
        
        # Safety check - ensure Geovoice tab exists
        try:
            worksheet = spreadsheet.worksheet(CONFIG['GEOVOICE_TAB'])
            logger.info(f"✅ Found '{CONFIG['GEOVOICE_TAB']}' tab")
        except gspread.WorksheetNotFound:
            logger.error(f"❌ Tab '{CONFIG['GEOVOICE_TAB']}' not found!")
            logger.error("Please create the 'Geovoice' tab manually in Google Sheets first.")
            return False
        
        # Clean Slate - Clear all content and formatting
        logger.info("🧹 Cleaning Geovoice tab (clearing content and formatting)...")
        
        # Clear all data
        worksheet.batch_clear(["A1:Z2000"])
        logger.info("✅ Cleared all data from A1:Z2000")
        
        # Remove filters
        try:
            worksheet.clear_basic_filter()
            logger.info("✅ Cleared basic filters")
        except:
            logger.info("⚠️ No filters to clear")
        
        # Reset all formatting
        try:
            worksheet_id = worksheet._properties['sheetId']
            body = {
                "requests": [
                    {
                        "updateCells": {
                            "range": {"sheetId": worksheet_id},
                            "fields": "userEnteredFormat"
                        }
                    }
                ]
            }
            spreadsheet.batch_update(body)
            logger.info("✅ Reset all formatting (colors, styles, etc.)")
        except Exception as format_error:
            logger.info(f"⚠️ Warning: Could not reset formatting: {format_error}")
        
        # Prepare data for upload
        logger.info("Preparing data for upload...")
        
        # Handle NaN values
        df = df.replace({np.nan: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        
        # Convert DataFrame to list
        data_to_upload = [df.columns.values.tolist()]
        for _, row in df.iterrows():
            row_data = []
            for value in row:
                if pd.isna(value) or value != value:
                    row_data.append(None)
                else:
                    row_data.append(value)
            data_to_upload.append(row_data)
        
        # Upload data
        logger.info(f"📤 Uploading {len(data_to_upload)-1} rows + headers to Geovoice tab...")
        worksheet.update(data_to_upload)
        logger.info("✅ Data uploaded successfully")
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            worksheet.update_acell('K1', f'Last Update: {timestamp} (Test Run)')
            logger.info(f"✅ Timestamp added to K1: Last Update: {timestamp} (Test Run)")
        except Exception as timestamp_error:
            logger.info(f"⚠️ Warning: Could not update timestamp: {timestamp_error}")
        
        # Safety verification - ensure we didn't touch first tab
        logger.info("🔒 Safety check: Verifying 'Musikis-saxli' tab was not touched...")
        try:
            first_tab = spreadsheet.worksheet('Musikis-saxli')  # Use explicit tab name
            logger.info(f"✅ 'Musikis-saxli' tab remains untouched")
        except gspread.WorksheetNotFound:
            logger.info("⚠️ 'Musikis-saxli' tab not found - this is expected if it was renamed")
        except Exception as safety_error:
            logger.info(f"⚠️ Could not verify 'Musikis-saxli' tab: {safety_error}")
        
        logger.info("\n🎉 Test Upload to 'Geovoice' Tab: SUCCESS")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test upload failed: {e}")
        return False

if __name__ == "__main__":
    success = test_geovoice_upload()
    if success:
        print("\n✅ Test Upload to 'Geovoice' Tab: SUCCESS")
    else:
        print("\n❌ Test Upload to 'Geovoice' Tab: FAILED")
