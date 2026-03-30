import subprocess
import sys
import os
import smtplib
import logging
import glob
import pytz
import gspread
import pandas as pd
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials
from email.message import EmailMessage
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
from dotenv import load_dotenv



load_dotenv()

# ==================== LOGGING CONFIGURATION ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
CONFIG = {
    'SENDER_EMAIL': os.getenv('SENDER_EMAIL', "iliamgeladze399@hotmail.com"),
    'RECIPIENT_EMAIL': os.getenv('RECIPIENT_EMAIL', "client-email@example.com"),
    'EMAIL_PASSWORD': os.getenv('MAIL_PASS'),
    'SPREADSHEET_ID': os.getenv('SPREADSHEET_ID', "1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94"),
    'TIMEZONE': os.getenv('TIMEZONE', 'Asia/Tbilisi'),
    'MAX_RETRIES': int(os.getenv('MAX_RETRIES', 2)),
    'ARCHIVE_DAYS': int(os.getenv('ARCHIVE_DAYS', 7)),
    'REQUIRED_FILES': ['credentials.json']
}

# ==================== HELPER FUNCTIONS ====================

def validate_environment():
    """Check if required files and environment variables exist."""
    missing = []
    # Check required files
    for file in CONFIG['REQUIRED_FILES']:
        if not os.path.exists(file):
            missing.append(f"File: {file}")
    # Check email password (optional but log if missing)
    if not CONFIG['EMAIL_PASSWORD']:
        logger.warning("Email password (MAIL_PASS) not set. Email notifications disabled.")
    if missing:
        logger.error(f"Missing required files/configs: {', '.join(missing)}")
        return False
    return True


def cleanup_old_reports(days=7):
    """Archive or delete reports older than specified days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    archived_count = 0
    
    # Create archive directory if it doesn't exist
    archive_dir = Path("archive")
    archive_dir.mkdir(exist_ok=True)
    
    # Find old report files
    report_patterns = ["FINAL_MATCH_REPORT_*.xlsx", "acoustic_inventory_*.xlsx", "geovoice_inventory_*.xlsx"]
    
    for pattern in report_patterns:
        for file in glob.glob(pattern):
            file_time = datetime.fromtimestamp(os.path.getctime(file))
            if file_time < cutoff_date:
                try:
                    # Move to archive instead of deleting
                    archive_path = archive_dir / file
                    if not archive_path.exists():
                        os.rename(file, archive_path)
                        archived_count += 1
                        logger.info(f"Archived: {file}")
                except Exception as e:
                    logger.warning(f"Could not archive {file}: {e}")
    
    if archived_count > 0:
        logger.info(f"Successfully archived {archived_count} old files")


def upload_to_google_sheets(file_path):
    """Upload report to Google Sheets with comprehensive NaN handling."""
    try:
        logger.info(f"Uploading to Google Sheets: {file_path}")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(CONFIG['SPREADSHEET_ID']).sheet1

        # Read file
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Comprehensive NaN handling to prevent JSON compliance error
        # Step 1: Replace pandas NaN with None
        df = df.replace({np.nan: None, pd.NaT: None})
        
        # Step 2: Handle any remaining null values
        df = df.where(pd.notnull(df), None)
        
        # Step 3: Convert DataFrame to list with proper JSON serialization
        data_to_upload = [df.columns.values.tolist()]
        
        # Convert each row to ensure NaN values become None
        for _, row in df.iterrows():
            row_data = []
            for value in row:
                if pd.isna(value) or value != value:  # Handle NaN cases
                    row_data.append(None)
                else:
                    row_data.append(value)
            data_to_upload.append(row_data)
        
        # Reset Google Sheets formatting and clear all data
        logger.info("Resetting Google Sheets (clearing formatting, filters, and data)...")
        
        # Clear all formatting, filters, and data from a wide range
        sheet.batch_clear(["A1:Z2000"])
        
        # Remove any active filters
        try:
            sheet.clear_basic_filter()
            logger.info("✅ Cleared basic filters")
        except:
            logger.info("⚠️  No filters to clear")
        
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
            logger.info("✅ Completely reset all formatting (colors, styles, etc.)")
        except Exception as format_error:
            logger.info(f"⚠️  Warning: Could not reset all formatting: {format_error}")
        
        # Upload data to Google Sheets starting from A1
        logger.info("Uploading data to Google Sheets...")
        sheet.update(data_to_upload)
        
        # Add timestamp to cell K1 (more visible than L1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            sheet.update_acell('K1', f'Last Update: {timestamp}')
            logger.info(f"Last Update timestamp added to cell K1: {timestamp}")
        except Exception as timestamp_error:
            logger.info(f"⚠️  Warning: Could not update timestamp: {timestamp_error}")
            logger.info("✅ Data upload still successful!")
        
        logger.info(f"Google Sheet updated successfully ({len(df)} rows)")
        return True
    except Exception as e:
        logger.error(f"Failed to update Google Sheet: {e}")
        return False


def send_email_report(file_path, status="success", error_details=""):
    """Send email report with status and optional error details."""
    if not CONFIG['EMAIL_PASSWORD']:
        logger.warning("Skipping email: MAIL_PASS not configured")
        return False

    try:
        logger.info(f"Sending email to {CONFIG['RECIPIENT_EMAIL']}...")

        msg = EmailMessage()

        if status == "success":
            msg['Subject'] = f"Daily Price Report - {datetime.now().strftime('%Y-%m-%d')}"
            content = "The automated price comparison update is complete. The Google Sheet is updated, and the file is attached."
        else:
            msg['Subject'] = f"Automation Alert - {datetime.now().strftime('%Y-%m-%d')}"
            content = f"The automation cycle encountered issues:\n\n{error_details}\n\nPlease check the logs for details."

        msg['From'] = CONFIG['SENDER_EMAIL']
        msg['To'] = CONFIG['RECIPIENT_EMAIL']
        msg.set_content(content)

        # Attach file if it exists and is a success report
        if status == "success" and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    filename=os.path.basename(file_path)
                )

        # Send via SMTP with Google App Password
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                smtp.starttls()
                smtp.login(CONFIG['SENDER_EMAIL'], CONFIG['EMAIL_PASSWORD'])
                smtp.send_message(msg)
                logger.info(f"Email sent successfully using Google App Password")
                return True
        except smtplib.SMTPAuthenticationError as auth_error:
            logger.error(f"SMTP Authentication failed: {auth_error}")
            logger.error("Please ensure you're using a Google App Password (16 characters) - not your regular password")
            return False

        except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def run_script(script_name, max_retries=None):
    """Run a Python script with retry logic and better error handling."""
    if max_retries is None:
        max_retries = CONFIG['MAX_RETRIES']
    
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        logger.info(f"EXECUTING: {script_name} (Attempt {attempt}/{max_retries + 1})")

        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"

            # If script_name is a string with spaces (i.e., has arguments), split it for subprocess
            if isinstance(script_name, str):
                import shlex
                script_args = shlex.split(script_name)
            else:
                script_args = script_name

            # Always prepend sys.executable
            cmd = [sys.executable] + script_args

            result = subprocess.run(
                cmd,
                check=True,
                env=env,
                capture_output=False,
                text=True,
                timeout=36000  # 10 hour timeout
            )

            logger.info(f"SUCCESS: {script_name} finished")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"TIMEOUT: {script_name} exceeded 1 hour limit")
            if attempt <= max_retries:
                logger.info(f"Retrying in 30 seconds...")
                time.sleep(30)
            continue
        except subprocess.CalledProcessError as e:
            logger.error(f"ERROR in {script_name}: Exit code {e.returncode}")
            if attempt <= max_retries:
                logger.info(f"Retrying in 30 seconds...")
                time.sleep(30)
            continue
        except Exception as e:
            logger.error(f"FATAL ERROR in {script_name}: {e}")
            return False

    logger.error(f"CRITICAL: {script_name} failed after {max_retries + 1} attempts")
    return False


def find_latest_report():
    """Find the most recently generated report file."""
    report_files = glob.glob("FINAL_MATCH_REPORT_*.xlsx")
    if not report_files:
        return None
    return max(report_files, key=os.path.getctime)


def main():
    """Main orchestration function with fresh execution model."""
    tz = pytz.timezone(CONFIG['TIMEZONE'])
    start_time = datetime.now(tz)
    
    logger.info("="*60)
    logger.info(f"AUTOMATION CYCLE STARTED: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    # Step 0: Validation and cleanup
    if not validate_environment():
        logger.error("Environment validation failed. Aborting.")
        return False

    # Generate unique session timestamp for this execution
    session_ts = datetime.now().strftime("%Y%m%d_%H%M")
    
    # Define files for THIS session only (no fallbacks)
    acoustic_file = f"acoustic_inventory_{session_ts}.xlsx"
    music_store_file = "music_store_inventory.csv"
    report_file = f"FINAL_MATCH_REPORT_{session_ts}.xlsx"

    logger.info(f"Session timestamp: {session_ts}")
    logger.info(f"Will create: {acoustic_file}")
    logger.info(f"Will create: {music_store_file}")
    logger.info(f"Will create: {report_file}")

    # Clean up old files to ensure fresh run
    cleanup_old_reports(days=1)
    
    # Delete existing music_store_inventory.csv to force fresh data
    if os.path.exists("music_store_inventory.csv"):
        logger.info("Removing existing music_store_inventory.csv to force fresh scraping...")
        os.remove("music_store_inventory.csv")
        logger.info("Deleted existing music_store_inventory.csv")

    execution_log = {}

    print("\n==================== STEP 1: Link Collection ====================", flush=True)
    execution_log['get_links'] = run_script("get_links.py")
    if not execution_log['get_links']:
        logger.error("Failed to get Acoustic links. Aborting.")
        send_email_report("", status="failure", error_details="Failed at Step 1: Link Collection (Acoustic)")
        return False

    execution_log['musikis_links'] = run_script("musikis-saxli-get-links.py")
    if not execution_log['musikis_links']:
        logger.error("Failed to get Musikis Saxli links. Aborting.")
        send_email_report("", status="failure", error_details="Failed at Step 1: Link Collection (Musikis Saxli)")
        return False

    execution_log['musikis_all_product_links'] = run_script("musikis-saxli-get-all-product-links.py")
    if not execution_log['musikis_all_product_links']:
        logger.error("Failed to get Musikis Saxli product links. Aborting.")
        send_email_report("", status="failure", error_details="Failed at Step 1: Product Link Collection (Musikis Saxli)")
        return False

    print("\n==================== STEP 2: Data Extraction ====================", flush=True)
    execution_log['scraper'] = run_script(f"scraper.py --output_file {acoustic_file}", max_retries=1)
    if not execution_log['scraper']:
        logger.error("Acoustic scrape failed. Aborting.")
        send_email_report("", status="failure", error_details="Failed at Step 2: Data Extraction (Acoustic)")
        return False

    execution_log['musikis_scraper'] = run_script("musikis-saxli-scraper.py", max_retries=1)
    if not execution_log['musikis_scraper']:
        logger.error("Musikis Saxli scrape failed. Aborting.")
        send_email_report("", status="failure", error_details="Failed at Step 2: Data Extraction (Musikis Saxli)")
        return False

    print("\n==================== STEP 3: Price Comparison ====================", flush=True)
    # Convert Musikis Saxli CSV to XLSX for comparison
    try:
        logger.info("Converting Music Store CSV to XLSX for comparison...")
        df = pd.read_csv(music_store_file, delimiter='\t', encoding='utf-16')
        # Fix column alignment for Music Store data
        df.columns = df.columns.str.strip()
        musikis_xlsx = music_store_file.replace('.csv', '.xlsx')
        df.to_excel(musikis_xlsx, index=False)
        logger.info(f"Converted to: {musikis_xlsx}")
    except Exception as e:
        logger.error(f"Failed to convert Musikis Saxli CSV to XLSX: {e}")
        send_email_report("", status="failure", error_details="Failed at Step 3: Musikis Saxli CSV to XLSX conversion")
        return False

    # Run price comparison
    try:
        cmd = [sys.executable, "compare_prices.py",
               "--acoustic_file", acoustic_file,
               "--musikis_file", musikis_xlsx,
               "--output_file", report_file]
        logger.info(f"Running price comparison: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        execution_log['compare'] = (result.returncode == 0)
    except Exception as e:
        logger.error(f"Price comparison failed: {e}")
        execution_log['compare'] = False
        send_email_report("", status="failure", error_details="Failed at Step 3: Price Comparison")
        return False

    print("\n==================== STEP 4: Reporting and Delivery ====================", flush=True)

    if os.path.exists(report_file):
        logger.info("Processing final report...")
        temp_df = pd.read_excel(report_file)

        # Clean column names
        temp_df.columns = temp_df.columns.str.strip()

        # Save and upload - prices are already handled correctly in compare_prices.py
        temp_df.to_excel(report_file, index=False)
        
        # Upload to Google Sheets
        upload_success = upload_to_google_sheets(report_file)
        execution_log['upload'] = upload_success
        
        if upload_success:
            logger.info("Successfully uploaded to Google Sheets")
            # Send success email
            email_success = send_email_report(report_file, status="success")
            execution_log['email'] = email_success
        else:
            logger.error("Google Sheets upload failed")
            # Send failure email
            send_email_report("", status="failure", error_details="Failed at Step 4: Google Sheets Upload")
            execution_log['email'] = False
        
    # Final Summary
    end_time = datetime.now(tz)
    duration = end_time - start_time
    
    logger.info("\n" + "="*60)
    logger.info("EXECUTION SUMMARY:")
    logger.info(f"   Link Collection: {'OK' if execution_log.get('get_links') else 'FAIL'}")
    logger.info(f"   Musikis Saxli Links: {'OK' if execution_log.get('musikis_links') else 'FAIL'}")
    logger.info(f"   Musikis Saxli Product Links: {'OK' if execution_log.get('musikis_all_product_links') else 'FAIL'}")
    logger.info(f"   Scraper (Acoustic): {'OK' if execution_log.get('scraper') else 'WARN'}")
    logger.info(f"   Scraper (Musikis Saxli): {'OK' if execution_log.get('musikis_scraper') else 'WARN'}")
    logger.info(f"   Price Comparison: {'OK' if execution_log.get('compare') else 'FAIL'}")
    logger.info(f"   Google Sheets Upload: {'OK' if execution_log.get('upload') else 'FAIL'}")
    logger.info(f"   Email Sent: {'OK' if execution_log.get('email') else 'WARN'}")
    logger.info(f"\nCYCLE FINISHED")
    logger.info(f"   Duration: {duration}")
    logger.info("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    import time
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f" CRITICAL ERROR: {e}", exc_info=True)
        sys.exit(1)
