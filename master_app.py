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
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
        sheet.clear()
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(data_to_upload)
        
        tbilisi_tz = pytz.timezone('Asia/Tbilisi')
        last_updated = datetime.now(tbilisi_tz).strftime('%Y-%m-%d %H:%M:%S')
        sheet.update_acell('Z1', f"Last Update: {last_updated}")
        logging.info("✅ Google Sheet successfully updated!")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to update Google Sheet: {e}")
        return False

def send_email_report(file_path):
    if not EMAIL_PASSWORD:
        logging.error("Email password not found (MAIL_PASS).")
        return False
    msg = EmailMessage()
    msg['Subject'] = f"Daily Price Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg.set_content("Automated report is ready.")
    try:
        with open(file_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=os.path.basename(file_path))
        with smtplib.SMTP("smtp.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)
            smtp.send_message(msg)
        logging.info("Report emailed.")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def run_script(script_name):
    logging.info(f"🚀 EXECUTING: {script_name}")
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.run([sys.executable, script_name], check=True, env=env)
        logging.info(f"✅ SUCCESS: {script_name} finished.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ CRITICAL ERROR in {script_name}")
        return False

def main():
    tbilisi_tz = pytz.timezone('Asia/Tbilisi')
    start_time = datetime.now(tbilisi_tz)
    logging.info(f"🌟 FULL CYCLE STARTED: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. ლინკების შეგროვება (ორივე საიტიდან)
    if not run_script("get_links.py"): return           # Acoustic-ის ლინკები
    if not run_script("geovoice_get_links.py"): return  # Geovoice-ის ლინკები
    
    # 2. დსკრაპვა
    if not run_script("scraper.py"): return             # Acoustic Scraper
    if not run_script("crawler.py"): return             # Geovoice Crawler
    
    # 3. შედარება
    if not run_script("compare_prices.py"): return

    # 4. რეპორტის გაგზავნა
    report_files = glob.glob("FINAL_MATCH_REPORT_*.xlsx")
    if report_files:
        latest_report = max(report_files, key=os.path.getctime)
        upload_to_google_sheets(latest_report)
        send_email_report(latest_report)
    
    logging.info(f"🏁 CYCLE FINISHED. Duration: {datetime.now(tbilisi_tz) - start_time}")

if __name__ == "__main__":
    main()