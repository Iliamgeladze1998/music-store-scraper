
import subprocess
import sys
import os
import smtplib
import logging
import glob
import pytz
import gspread
import pandas as pd
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
        logger.warning("⚠️ Email password (MAIL_PASS) not set. Email notifications disabled.")
    if missing:
        logger.error(f"❌ Missing required files/configs: {', '.join(missing)}")
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
                        logger.info(f"📦 Archived: {file}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not archive {file}: {e}")
    
    if archived_count > 0:
        logger.info(f"📦 Successfully archived {archived_count} old files")


def upload_to_google_sheets(file_path):
    """Upload report to Google Sheets with better error handling."""
    try:
        logger.info(f"📊 Uploading to Google Sheets: {file_path}")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(CONFIG['SPREADSHEET_ID']).sheet1

        # Read file
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        # Prepare and upload data
        sheet.clear()
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(data_to_upload)
        
        logger.info(f"✅ Google Sheet updated successfully ({len(df)} rows)")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to update Google Sheet: {e}")
        return False


def send_email_report(file_path, status="success", error_details=""):
    """Send email report with status and optional error details."""
    if not CONFIG['EMAIL_PASSWORD']:
        logger.warning("⚠️ Skipping email: MAIL_PASS not configured")
        return False

    try:
        logger.info(f"📧 Sending email to {CONFIG['RECIPIENT_EMAIL']}...")

        msg = EmailMessage()

        if status == "success":
            msg['Subject'] = f"✅ Daily Price Report - {datetime.now().strftime('%Y-%m-%d')}"
            content = "The automated price comparison update is complete. The Google Sheet is updated, and the file is attached."
        else:
            msg['Subject'] = f"⚠️ Automation Alert - {datetime.now().strftime('%Y-%m-%d')}"
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

        # Send via SMTP
        with smtplib.SMTP("smtp.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(CONFIG['SENDER_EMAIL'], CONFIG['EMAIL_PASSWORD'])
            smtp.send_message(msg)

        logger.info(f"✅ Email sent successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False


def run_script(script_name, max_retries=None):
    """Run a Python script with retry logic and better error handling."""
    if max_retries is None:
        max_retries = CONFIG['MAX_RETRIES']
    
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        logger.info(f"🚀 EXECUTING: {script_name} (Attempt {attempt}/{max_retries + 1})")
        
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"
            
            # Run with captured output for better logging
            result = subprocess.run(
                [sys.executable, script_name],
                check=True,
                env=env,
                capture_output=False,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            logger.info(f"✅ SUCCESS: {script_name} finished")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ TIMEOUT: {script_name} exceeded 1 hour limit")
            if attempt <= max_retries:
                logger.info(f"🔄 Retrying in 30 seconds...")
                time.sleep(30)
            continue
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ ERROR in {script_name}: Exit code {e.returncode}")
            if attempt <= max_retries:
                logger.info(f"🔄 Retrying in 30 seconds...")
                time.sleep(30)
            continue
        except Exception as e:
            logger.error(f"❌ FATAL ERROR in {script_name}: {e}")
            return False
    
    logger.error(f"❌ CRITICAL: {script_name} failed after {max_retries + 1} attempts")
    return False


def find_latest_report():
    """Find the most recently generated report file."""
    report_files = glob.glob("FINAL_MATCH_REPORT_*.xlsx")
    if not report_files:
        return None
    return max(report_files, key=os.path.getctime)


def main():
    """Main orchestration function with better error tracking."""
    tz = pytz.timezone(CONFIG['TIMEZONE'])
    start_time = datetime.now(tz)
    
    logger.info("="*60)
    logger.info(f"🌟 AUTOMATION CYCLE STARTED: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # Step 0: Validation and cleanup
    if not validate_environment():
        logger.error("❌ Environment validation failed. Aborting.")
        return False
    
    # Cleanup old files
    cleanup_old_reports(days=CONFIG['ARCHIVE_DAYS'])
    
    # Clean old link files
    for f in ["subcategory_links.txt", "all_pages_to_scrape.txt"]:
        if os.path.exists(f):
            os.remove(f)
            logger.info(f"🗑️ Deleted old file: {f}")
    
    execution_log = {}
    
    # Step 1: Link Collection
    logger.info("\n📍 STEP 1: Link Collection")
    execution_log['get_links'] = run_script("get_links.py")
    if not execution_log['get_links']:
        logger.error("❌ Failed to get Acoustic links. Aborting.")
        send_email_report("", status="failure", error_details="Failed at Step 1: Link Collection (Acoustic)")
        return False
    
    execution_log['geovoice_links'] = run_script("geovoice_get_links.py")
    if not execution_log['geovoice_links']:
        logger.error("❌ Failed to get Geovoice links. Aborting.")
        send_email_report("", status="failure", error_details="Failed at Step 1: Link Collection (Geovoice)")
        return False
    
    # Step 2: Data Extraction (Scraping) - Can run in parallel
    logger.info("\n📍 STEP 2: Data Extraction")
    import time
    
    # Start both scrapers (they'll run sequentially, but structure allows for async in future)
    execution_log['scraper'] = run_script("scraper.py", max_retries=1)
    if not execution_log['scraper']:
        logger.warning("⚠️ Warning: scraper.py failed, but continuing...")
    
    execution_log['crawler'] = run_script("crawler.py", max_retries=1)
    if not execution_log['crawler']:
        logger.warning("⚠️ Warning: crawler.py failed, but continuing...")
    
    if not (execution_log['scraper'] or execution_log['crawler']):
        logger.error("❌ Both scrapers failed. No data to compare.")
        send_email_report("", status="failure", error_details="Failed at Step 2: No valid scraping data")
        return False
    
    # Step 3: Price Comparison
    logger.info("\n📍 STEP 3: Price Comparison")
    execution_log['compare'] = run_script("compare_prices.py")
    if not execution_log['compare']:
        logger.error("❌ Price comparison failed.")
        send_email_report("", status="failure", error_details="Failed at Step 3: Price Comparison")
        return False
    
    # Step 4: Reporting and Delivery
    logger.info("\n📍 STEP 4: Reporting and Delivery")
    latest_report = find_latest_report()
    
    if latest_report:
        logger.info(f"📊 Found report: {latest_report}")
        
        # Upload to Google Sheets
        sheets_success = upload_to_google_sheets(latest_report)
        
        # Send email
        email_success = send_email_report(latest_report, status="success")
        
        execution_log['upload'] = sheets_success
        execution_log['email'] = email_success
    else:
        logger.error("❌ No report files found for delivery")
        send_email_report("", status="failure", error_details="Failed at Step 4: No report file generated")
        return False
    
    # Final Summary
    end_time = datetime.now(tz)
    duration = end_time - start_time
    
    logger.info("\n" + "="*60)
    logger.info("📋 EXECUTION SUMMARY:")
    logger.info(f"   Link Collection: {'✅' if execution_log.get('get_links') else '❌'}")
    logger.info(f"   Geovoice Links: {'✅' if execution_log.get('geovoice_links') else '❌'}")
    logger.info(f"   Scraper: {'✅' if execution_log.get('scraper') else '⚠️'}")
    logger.info(f"   Crawler: {'✅' if execution_log.get('crawler') else '⚠️'}")
    logger.info(f"   Price Comparison: {'✅' if execution_log.get('compare') else '❌'}")
    logger.info(f"   Google Sheets Upload: {'✅' if execution_log.get('upload') else '❌'}")
    logger.info(f"   Email Sent: {'✅' if execution_log.get('email') else '⚠️'}")
    logger.info(f"\n🏁 CYCLE FINISHED")
    logger.info(f"   ⏱️  Duration: {duration}")
    logger.info("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    import time
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"🔥 CRITICAL ERROR: {e}", exc_info=True)
        sys.exit(1)