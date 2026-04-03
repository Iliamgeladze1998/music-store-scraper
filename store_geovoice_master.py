import subprocess
import sys
import os
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geovoice_automation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'SPREADSHEET_ID': "1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94",
    'CREDENTIALS_FILE': "credentials.json",
    'GEOVOICE_TAB': "Geovoice"
}

def run_script(script_name):
    """Run a Python script."""
    logger.info(f"Executing: {script_name}")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False,
            text=True,
            timeout=3600
        )
        logger.info(f"SUCCESS: {script_name} completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR in {script_name}: Exit code {e.returncode}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: {script_name} exceeded 1 hour")
        return False
    except Exception as e:
        logger.error(f"FATAL ERROR in {script_name}: {e}")
        return False

def upload_to_geovoice_tab(file_path):
    """Upload report specifically to Geovoice tab with clean formatting."""
    try:
        logger.info(f"Uploading to Geovoice tab: {file_path}")
        
        # Authenticate with Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CONFIG['CREDENTIALS_FILE'], scope)
        client = gspread.authorize(creds)
        
        # Open spreadsheet and get Geovoice tab
        spreadsheet = client.open_by_key(CONFIG['SPREADSHEET_ID'])
        
        # Try to get Geovoice tab, with safety check
        try:
            worksheet = spreadsheet.worksheet(CONFIG['GEOVOICE_TAB'])
            logger.info(f"SUCCESS: Found existing Geovoice tab: {CONFIG['GEOVOICE_TAB']}")
        except gspread.WorksheetNotFound:
            logger.error(f"ERROR: Geovoice tab '{CONFIG['GEOVOICE_TAB']}' not found!")
            logger.error("Please create the 'Geovoice' tab manually in Google Sheets first.")
            logger.error("DO NOT proceed - this prevents accidental overwriting of wrong tab.")
            return False
        
        # Read the report file
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
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
        
        # COMPLETELY RESET Geovoice tab formatting
        logger.info("Resetting Geovoice tab (clearing formatting, filters, and data)...")
        
        # Clear all formatting, filters, and data from Geovoice tab
        worksheet.batch_clear(["A1:Z2000"])
        
        # Remove any active filters
        try:
            worksheet.clear_basic_filter()
            logger.info("SUCCESS: Cleared basic filters on Geovoice tab")
        except:
            logger.info("INFO: No filters to clear on Geovoice tab")
        
        # Complete formatting reset - remove all background colors, styles, etc.
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
            logger.info("SUCCESS: Completely reset all formatting on Geovoice tab (colors, styles, etc.)")
        except Exception as format_error:
            logger.info(f"WARNING: Could not reset all formatting on Geovoice tab: {format_error}")
        
        # Upload fresh data to Geovoice tab
        logger.info("Uploading data to Geovoice tab...")
        worksheet.update(data_to_upload)
        
        # Add timestamp to cell K1 of Geovoice tab
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            worksheet.update_acell('K1', f'Last Update: {timestamp}')
            logger.info(f"SUCCESS: Timestamp added to Geovoice tab cell K1: Last Update: {timestamp}")
        except Exception as timestamp_error:
            logger.info(f"WARNING: Could not update timestamp on Geovoice tab: {timestamp_error}")
            logger.info("SUCCESS: Data upload to Geovoice tab still successful!")
        
        logger.info(f"SUCCESS: Geovoice tab updated successfully ({len(df)} rows)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload to Geovoice tab: {e}")
        return False

def main():
    """Main orchestration for Geovoice workflow."""
    logger.info("="*60)
    logger.info("GEOVOICE AUTOMATION CYCLE STARTED")
    logger.info("="*60)
    
    # Generate session timestamp
    session_ts = datetime.now().strftime("%Y%m%d_%H%M")
    
    # Define files for this session
    acoustic_file = f"acoustic_inventory_{session_ts}.xlsx"
    geovoice_file = "geovoice_inventory.csv"
    report_file = f"GEOVOICE_REPORT_{session_ts}.xlsx"
    
    logger.info(f"Session timestamp: {session_ts}")
    logger.info(f"Will create: {acoustic_file}")
    logger.info(f"Will create: {geovoice_file}")
    logger.info(f"Will create: {report_file}")
    
    execution_log = {}
    
    # Step 1: Always run fresh Acoustic link collection (no caching)
    print("\n==================== STEP 1: Acoustic Link Collection ====================", flush=True)
    execution_log['acoustic_links'] = run_script("store_acoustic_links.py")
    if not execution_log['acoustic_links']:
        logger.error("Failed to get Acoustic links. Aborting.")
        return False
    
    # Step 2: Get Geovoice links
    print("\n==================== STEP 2: Geovoice Link Collection ====================", flush=True)
    execution_log['geovoice_links'] = run_script("store_geovoice_links.py")
    if not execution_log['geovoice_links']:
        logger.error("Failed to get Geovoice links. Aborting.")
        return False
    
    # Step 3: Get all Geovoice product links
    print("\n==================== STEP 3: Geovoice Product Link Collection ====================", flush=True)
    execution_log['geovoice_product_links'] = run_script("store_geovoice_all_links.py")
    if not execution_log['geovoice_product_links']:
        logger.error("Failed to get Geovoice product links. Aborting.")
        return False
    
    # Step 4: Run acoustic scraper
    print("\n==================== STEP 4: Acoustic Data Extraction ====================", flush=True)
    acoustic_cmd = [sys.executable, "store_acoustic_scraper.py", "--output_file", acoustic_file]
    logger.info(f"Executing: {' '.join(acoustic_cmd)}")
    try:
        result = subprocess.run(acoustic_cmd, check=True, capture_output=False, text=True, timeout=3600)
        logger.info(f"SUCCESS: store_acoustic_scraper.py completed")
        execution_log['acoustic'] = True
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR in store_acoustic_scraper.py: Exit code {e.returncode}")
        execution_log['acoustic'] = False
    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: store_acoustic_scraper.py exceeded 1 hour")
        execution_log['acoustic'] = False
    except Exception as e:
        logger.error(f"FATAL ERROR in store_acoustic_scraper.py: {e}")
        execution_log['acoustic'] = False
    
    if not execution_log['acoustic']:
        logger.error("Acoustic scrape failed. Aborting.")
        return False
    
    # Step 5: Run Geovoice scraper
    print("\n==================== STEP 5: Geovoice Data Extraction ====================", flush=True)
    execution_log['geovoice'] = run_script("store_geovoice_scraper.py")
    if not execution_log['geovoice']:
        logger.error("Geovoice scrape failed. Aborting.")
        return False
    
    # Step 6: Run price comparison with standardized structure
    print("\n==================== STEP 6: Price Comparison ====================", flush=True)
    try:
        # Use our standardized comparison logic
        logger.info("Running standardized Geovoice price comparison...")
        
        # Add current directory to path for imports
        sys.path.append('.')
        
        # Load and run the comparison logic directly
        from test_geovoice_compare import test_geovoice_comparison
        
        # Run the comparison and save to our report file
        if test_geovoice_comparison():
            # Copy the test result to our session report file
            import shutil
            shutil.copy("TEST_GEOVOICE_REPORT.xlsx", report_file)
            logger.info(f"Standardized comparison completed: {report_file}")
            execution_log['compare'] = True
        else:
            logger.error("Standardized comparison failed")
            execution_log['compare'] = False
            return False
            
    except Exception as e:
        logger.error(f"Price comparison failed: {e}")
        execution_log['compare'] = False
        return False
    
    # Step 7: Upload to Geovoice tab
    print("\n==================== STEP 7: Upload to Geovoice Tab ====================", flush=True)
    execution_log['upload'] = upload_to_geovoice_tab(report_file)
    
    # Final Summary
    end_time = datetime.now()
    duration = end_time - datetime.now().replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second)
    
    logger.info("\n" + "="*60)
    logger.info("GEOVOICE EXECUTION SUMMARY:")
    logger.info(f"   Acoustic Links: {'OK' if execution_log.get('acoustic_links') else 'FAIL'}")
    logger.info(f"   Geovoice Links: {'OK' if execution_log.get('geovoice_links') else 'FAIL'}")
    logger.info(f"   Geovoice Product Links: {'OK' if execution_log.get('geovoice_product_links') else 'FAIL'}")
    logger.info(f"   Acoustic Scraper: {'OK' if execution_log.get('acoustic') else 'FAIL'}")
    logger.info(f"   Geovoice Scraper: {'OK' if execution_log.get('geovoice') else 'FAIL'}")
    logger.info(f"   Price Comparison: {'OK' if execution_log.get('compare') else 'FAIL'}")
    logger.info(f"   Geovoice Tab Upload: {'OK' if execution_log.get('upload') else 'FAIL'}")
    logger.info(f"\nGEOVOICE CYCLE FINISHED")
    logger.info(f"   Duration: {duration}")
    logger.info("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: {e}", exc_info=True)
        sys.exit(1)
