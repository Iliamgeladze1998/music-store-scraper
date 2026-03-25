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
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration
SENDER_EMAIL = "iliamgeladze399@hotmail.com" 
RECIPIENT_EMAIL = "client-email@example.com" 
EMAIL_PASSWORD = os.getenv('MAIL_PASS') 
SPREADSHEET_ID = "1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94" 

def upload_to_google_sheets(file_path):
    """ატვირთავს რეპორტს პირდაპირ Google Sheets-ში და წერს განახლების დროს."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1

        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        sheet.clear()
        
        # მონაცემების მომზადება და ატვირთვა
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(data_to_upload)
        
        # --- აი აქ ვამატებთ დროის ჩაწერას ---
        try:
            tbilisi_tz = pytz.timezone('Asia/Tbilisi')
            last_updated = datetime.now(tbilisi_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            # ჩაწერს Z1 უჯრაში, რომ მონაცემებს ხელი არ შეუშალოს
            # თუ გინდა სხვაგან იყოს, შეცვალე 'Z1'
            sheet.update_acell('Z1', f"ბოლო განახლება: {last_updated}")
            logging.info(f"🕒 Timestamp added: {last_updated}")
        except Exception as timestamp_error:
            logging.warning(f"⚠️ Could not add timestamp: {timestamp_error}")
        # ----------------------------------

        logging.info("✅ Google Sheet successfully updated!")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to update Google Sheet: {e}")
        return False

def send_email_report(file_path):
    """Handles the SMTP connection and sends the attachment via Hotmail/Outlook."""
    if not EMAIL_PASSWORD:
        logging.error("Email password not found in environment variables (MAIL_PASS).")
        return False

    msg = EmailMessage()
    msg['Subject'] = f"Daily Price Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg.set_content("The automated price comparison update is complete. The Google Sheet is updated, and the file is attached.")

    try:
        with open(file_path, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='application',
                subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                filename=os.path.basename(file_path)
            )

        with smtplib.SMTP("smtp.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)
            smtp.send_message(msg)
        logging.info(f"Report successfully emailed to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def validate_report(file_path):
    if not os.path.exists(file_path):
        logging.error(f"Validation Error: File {file_path} not found.")
        return False
    return True

def run_script(script_name):
    """Executes sub-scripts and allows them to open browser windows."""
    logging.info(f"EXECUTING: {script_name}")
    try:
        # მოვაშორეთ capture_output, რომ Playwright-ის ბრაუზერი გამოჩნდეს
        result = subprocess.run([sys.executable, script_name], check=True)
        logging.info(f"SUCCESS: {script_name} finished.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"CRITICAL ERROR in {script_name}")
        return False

def main():
    # 1. განვსაზღვროთ თბილისის დროის სარტყელი
    tbilisi_tz = pytz.timezone('Asia/Tbilisi')
    
    # 2. ავიღოთ მიმდინარე დრო თბილისის დროით
    start_time = datetime.now(tbilisi_tz)
    
    logging.info(f"🚀 Market Update Sequence Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # --- Steps 1-3 (Scraping & Comparison) ---
    if not run_script("get_links.py"): return
    if not run_script("geovoice_get_links.py"): return
    if not run_script("scraper.py"): return
    if not run_script("crawler.py"): return
    if not run_script("compare_prices.py"): return

    # --- Step 4: Delivery ---
    report_files = glob.glob("FINAL_MATCH_REPORT_*.xlsx") or glob.glob("STRICT_REPORT_*.xlsx")
    
    if report_files:
        latest_report = max(report_files, key=os.path.getctime)
        if validate_report(latest_report):
            upload_to_google_sheets(latest_report)
            send_email_report(latest_report)
    else:
        logging.error("❌ No report files found for delivery.")

    # 3. დასრულების დროსაც თბილისის დროით ვითვლით
    end_time = datetime.now(tbilisi_tz)
    duration = end_time - start_time
    logging.info(f"✅ WORKFLOW FINISHED AT: {end_time.strftime('%H:%M:%S')}. Duration: {duration}")

if __name__ == "__main__":
    main()