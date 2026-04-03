import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import logging
import sys
import io

# Fix UTF-8 encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def upload_to_google_sheets(comparison_file, sheet_name="Mireli"):
    """Upload comparison data to Google Sheets with EXACT column structure"""
    logger.info(f"--- Uploading to Google Sheets Tab: {sheet_name} ---")
    
    try:
        # Load comparison data
        if comparison_file.endswith('.xlsx'):
            df = pd.read_excel(comparison_file)
        else:
            df = pd.read_csv(comparison_file)
        
        logger.info(f"Loaded {len(df)} comparison rows")
        
        # Create processed DataFrame with EXACT column order
        processed_df = pd.DataFrame()
        
        # 1. UNIQUE_ID
        if 'UNIQUE_ID' in df.columns:
            processed_df['UNIQUE_ID'] = df['UNIQUE_ID']
        else:
            processed_df['UNIQUE_ID'] = df.get('ID', '')
        
        # 2. Product_Name (Acoustic product name)
        if 'Product_Name' in df.columns:
            processed_df['Product_Name'] = df['Product_Name']
        else:
            processed_df['Product_Name'] = df.get('NAME', '')
        
        # 3. Price_Acoustic
        if 'ACOUSTIC_PRICE' in df.columns:
            processed_df['Price_Acoustic'] = df['ACOUSTIC_PRICE'].fillna(0)
        elif 'Price_Acoustic' in df.columns:
            processed_df['Price_Acoustic'] = df['Price_Acoustic'].fillna(0)
        else:
            processed_df['Price_Acoustic'] = df.get('PRICE', 0)
        
        # 4. Price_Mireli
        if 'MIRELI_PRICE' in df.columns:
            processed_df['Price_Mireli'] = df['MIRELI_PRICE'].fillna(0)
        elif 'Price_Mireli' in df.columns:
            processed_df['Price_Mireli'] = df['Price_Mireli'].fillna(0)
        else:
            processed_df['Price_Mireli'] = df.get('PRICE', 0)
        
        # 5. Price_Diff
        if 'Price_Diff' in df.columns:
            processed_df['Price_Diff'] = df['Price_Diff'].fillna(0)
        elif 'PRICE_DIFF' in df.columns:
            processed_df['Price_Diff'] = df['PRICE_DIFF'].fillna(0)
        else:
            processed_df['Price_Diff'] = processed_df['Price_Mireli'].fillna(0) - processed_df['Price_Acoustic'].fillna(0)
        
        # 6. Status_Acoustic
        if 'ACOUSTIC_STATUS' in df.columns:
            processed_df['Status_Acoustic'] = df['ACOUSTIC_STATUS'].fillna('Unknown')
        elif 'Status_Acoustic' in df.columns:
            processed_df['Status_Acoustic'] = df['Status_Acoustic'].fillna('Unknown')
        else:
            processed_df['Status_Acoustic'] = df.get('STATUS', 'Unknown')
        
        # 7. Status_Mireli
        if 'MIRELI_STATUS' in df.columns:
            processed_df['Status_Mireli'] = df['MIRELI_STATUS'].fillna('Unknown')
        elif 'Status_Mireli' in df.columns:
            processed_df['Status_Mireli'] = df['Status_Mireli'].fillna('Unknown')
        else:
            processed_df['Status_Mireli'] = df.get('STATUS', 'Unknown')
        
        # 8. Link_Acoustic
        if 'ACOUSTIC_LINK' in df.columns:
            processed_df['Link_Acoustic'] = df['ACOUSTIC_LINK'].fillna('')
        elif 'Link_Acoustic' in df.columns:
            processed_df['Link_Acoustic'] = df['Link_Acoustic'].fillna('')
        else:
            processed_df['Link_Acoustic'] = df.get('LINK', '')
        
        # 9. Link_Mireli
        if 'MIRELI_LINK' in df.columns:
            processed_df['Link_Mireli'] = df['MIRELI_LINK'].fillna('')
        elif 'Link_Mireli' in df.columns:
            processed_df['Link_Mireli'] = df['Link_Mireli'].fillna('')
        else:
            processed_df['Link_Mireli'] = df.get('LINK', '')
        
        # 10. Status_Filter (DEFAULT TO 'OK' - FOR USER FEEDBACK)
        if 'Status_Filter' in df.columns:
            processed_df['Status_Filter'] = df['Status_Filter'].fillna('OK')
        elif 'Match_Confidence' in df.columns:
            processed_df['Status_Filter'] = df['Match_Confidence'].fillna('OK')
        else:
            processed_df['Status_Filter'] = 'OK'  # Default to OK
        
        # 11. Last_Updated
        processed_df['Last_Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        def create_link(url):
            if pd.notna(url) and url != '' and str(url).startswith('http'):
                return str(url)
            else:
                return ''
        
        processed_df['Link_Acoustic'] = processed_df['Link_Acoustic'].apply(create_link)
        processed_df['Link_Mireli'] = processed_df['Link_Mireli'].apply(create_link)
        
        # Load Google Sheets credentials
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        # Open spreadsheet and worksheet
        spreadsheet = client.open_by_key("1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94")
        worksheet = spreadsheet.worksheet(sheet_name)
        
        logger.info(f"Found existing worksheet: {sheet_name}")
        
        # Clear existing content
        worksheet.clear()
        logger.info("Clearing existing content...")
        
        # Prepare data for upload
        headers = ['UNIQUE_ID', 'Product_Name', 'Price_Acoustic', 'Price_Mireli', 'Price_Diff', 
                  'Status_Acoustic', 'Status_Mireli', 'Link_Acoustic', 'Link_Mireli', 'Status_Filter', 'Last_Updated']
        
        data_to_upload = [headers] + processed_df.values.tolist()
        
        # Upload data
        worksheet.update('A1', data_to_upload, value_input_option='USER_ENTERED')
        logger.info("Uploading main data...")
        
        # Add timestamp
        timestamp_data = [['Last Updated:', datetime.now().strftime('%Y-%m-%d %H:%M')]]
        worksheet.update('K1', timestamp_data, value_input_option='USER_ENTERED')
        logger.info("Adding timestamp...")
        
        logger.info(f"SUCCESS! Uploaded {len(processed_df)} rows + headers to Google Sheets")
        logger.info(f"Worksheet URL: https://docs.google.com/spreadsheets/d/1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94")
        logger.info(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error uploading to Google Sheets: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--comparison_file', required=True, help='Path to comparison file')
    parser.add_argument('--sheet_name', default='Mireli', help='Google Sheet worksheet name')
    args = parser.parse_args()
    
    success = upload_to_google_sheets(args.comparison_file, args.sheet_name)
    if success:
        print("SUCCESS: Upload completed successfully")
    else:
        print("ERROR: Upload failed")
