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

        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)

        sheet.clear()
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(data_to_upload)
        
        # დროის ჩაწერა Z1 უჯრაში
        try:
            tbilisi_tz = pytz.timezone('Asia/Tbilisi')
            last_updated = datetime.now(tbilisi_tz).strftime('%Y-%m-%d %H:%M:%S')
            sheet.update_acell('Z1', f"Last Update: {last_updated}")
            logging.info(f"🕒 Timestamp added: {last_updated}")
        except Exception as timestamp_error:
            logging.warning(f"⚠️ Could not add timestamp: {timestamp_error}")

        logging.info("✅ Google Sheet successfully updated!")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to update Google Sheet: {e}")
        return False

def send_email_report(file_path):
    """აგზავნის რეპორტს მეილზე (Hotmail/Outlook)."""
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

def run_script(script_name):
    """ასრულებს ქვე-სკრიპტებს."""
    logging.info(f"🚀 EXECUTING: {script_name}")
    try:
        # ვიყენებთ utf-8 ენკოდინგს პრინტებისთვის
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.run([sys.executable, script_name], check=True, env=env)
        logging.info(f"✅ SUCCESS: {script_name} finished.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ CRITICAL ERROR in {script_name}: {e}")
        return False

def main():
    tbilisi_tz = pytz.timezone('Asia/Tbilisi')
    start_time = datetime.now(tbilisi_tz)
    
    logging.info(f"🌟 Market Update Sequence Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. ვაგროვებთ მონაცემებს ორივე საიტიდან
    if not run_script("scraper.py"): return  # Acoustic Scraper
    if not run_script("crawler.py"): return  # Geovoice Crawler (with inner SKU search)
    
    # 2. ვადარებთ ფასებს
    if not run_script("compare_prices.py"): return

    # 3. ვეძებთ ბოლო გენერირებულ რეპორტს
    report_files = glob.glob("FINAL_MATCH_REPORT_*.xlsx")
    
    if report_files:
        latest_report = max(report_files, key=os.path.getctime)
        # 4. ავტვირთავთ და ვაგზავნით მეილზე
        upload_to_google_sheets(latest_report)
        send_email_report(latest_report)
    else:
        logging.error("❌ No report files found for delivery.")

    end_time = datetime.now(tbilisi_tz)
    duration = end_time - start_time
    logging.info(f"🏁 WORKFLOW FINISHED AT: {end_time.strftime('%H:%M:%S')}. Duration: {duration}")

if __name__ == "__main__":
    main()