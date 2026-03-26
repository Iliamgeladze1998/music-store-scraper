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

def run_script(script_name):
    logging.info(f"🚀 EXECUTING: {script_name}")
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.run([sys.executable, script_name], check=True, env=env)
        logging.info(f"✅ SUCCESS: {script_name} finished.")
        return True
    except subprocess.CalledProcessError:
        logging.error(f"❌ CRITICAL ERROR in {script_name}")
        return False

def main():
    tbilisi_tz = pytz.timezone('Asia/Tbilisi')
    start_time = datetime.now(tbilisi_tz)
    logging.info(f"🌟 FULL CYCLE STARTED: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # --- ნაბიჯი 0: ძველი ლინკების წაშლა, რომ სუფთად დაიწყოს ---
    for f in ["subcategory_links.txt", "all_pages_to_scrape.txt"]:
        if os.path.exists(f):
            os.remove(f)
            logging.info(f"🗑️ Deleted old file: {f}")

    # 1. ლინკების თავიდან მოძიება (ახლა ესენი აღარ გამოიპარება)
    if not run_script("get_links.py"): return           # Acoustic links
    if not run_script("geovoice_get_links.py"): return  # Geovoice links
    
    # 2. დსკრაპვა (უკვე ახალი ლინკებით)
    if not run_script("scraper.py"): return             # Acoustic scan
    if not run_script("crawler.py"): return             # Geovoice scan (with UNIQUE_ID)
    
    # 3. შედარება
    if not run_script("compare_prices.py"): return

    # 4. რეპორტინგი
    report_files = glob.glob("FINAL_MATCH_REPORT_*.xlsx")
    if report_files:
        latest_report = max(report_files, key=os.path.getctime)
        # აქ დაამატე upload_to_google_sheets და send_email_report ფუნქციები
        logging.info(f"📊 Final report ready: {latest_report}")
    
    logging.info(f"🏁 CYCLE FINISHED. Duration: {datetime.now(tbilisi_tz) - start_time}")

if __name__ == "__main__":
    main()