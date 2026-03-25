import subprocess
import time
import sys
import os
from datetime import datetime

def run_script(script_name):
    """ გაშვება და შეცდომების კონტროლი """
    print(f"\n" + "="*60)
    print(f"🚀 EXECUTING: {script_name}")
    print("="*60)
    
    try:
        # sys.executable იყენებს შენს venv-ს
        subprocess.run([sys.executable, script_name], check=True)
        print(f"\n✅ {script_name} DONE")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR in {script_name}: {e}")
        return False

def main():
    start_time = datetime.now()
    print(f"🔔 Full Market Update Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # --- ნაბიჯი 1: ლინკების განახლება ---
    # Acoustic-ის მენიუს სკანირება
    if not run_script("get_links.py"): return

    # Geovoice-ის პაგინაციის სკანირება
    if not run_script("geovoice_get_links.py"): return

    # --- ნაბიჯი 2: სრული სკრაპინგი (UNIQUE_ID-ებით) ---
    # Acoustic-ის ყველა პროდუქტი
    if not run_script("scraper.py"): return

    # Geovoice-ის ყველა პროდუქტი (ყველაზე ხანგრძლივი ნაწილი)
    if not run_script("crawler.py"): return

    # --- ნაბიჯი 3: მონაცემთა შედარება ---
    print("\n⚖️ Generating Comparison Report...")
    if not run_script("compare_prices.py"): return

    # --- ნაბიჯი 4: Git Automation (თუ გჭირდება GitHub-ზე ატვირთვა) ---
    """
    print("\n📦 Pushing updates to GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-update: {datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ GitHub update complete!")
    except Exception as e:
        print(f"⚠️ Git push failed: {e}")
    """

    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n" + "🏆"*20)
    print(f"FINISHED SUCCESSFULLY!")
    print(f"Total processing time: {duration}")
    print("🏆"*20)

if __name__ == "__main__":
    main()