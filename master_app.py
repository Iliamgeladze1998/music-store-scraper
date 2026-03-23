import subprocess
import sys
import time
import os
from datetime import datetime

def run_step(command, is_git=False):
    """Executes a Python script or a Git command with error handling"""
    print(f"\n{'='*60}")
    print(f"🚀 {'GIT OPERATION' if is_git else 'PROCESS STARTED'}: {command}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        if is_git:
            # Execute Git commands using shell
            subprocess.run(command, shell=True, check=True)
        else:
            # Execute Python scripts using the current environment's executable
            if not os.path.exists(command):
                print(f"❌ Error: Script '{command}' not found in the directory!")
                return False
            subprocess.run([sys.executable, command], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Execution failed for: {command}")
        return False

def main():
    start_time = time.time()
    
    # 📝 STEP 1: Data Collection & AI-Enhanced Comparison
    # These scripts will run sequentially
    pipeline = [
        "get_links.py",           # Acoustic.ge Links Collector
        "geovoice_get_links.py",   # Geovoice.ge Links Collector
        "scraper.py",             # Acoustic.ge Data Scraper
        "crawler.py",             # Geovoice.ge Data Scraper
        "compare_prices.py"       # Smart Price Comparison Engine (The new version)
    ]
    
    for script in pipeline:
        if not run_step(script):
            print(f"\n🛑 PIPELINE HALTED: Error detected in '{script}'")
            print("Please fix the issue before running the Master App again.")
            sys.exit(1)

    # 📝 STEP 2: Automated Cloud Sync (GitHub)
    print("\n☁️ SYNCING RESULTS TO GITHUB...")
    
    # Identify the current branch to avoid pushing to the wrong place
    # Currently working on: feature/strict-matching
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    current_branch = "feature/strict-matching" 
    
    git_commands = [
        "git add .",
        f'git commit -m "Auto-update: Smart Market Analysis {timestamp}"',
        f"git push origin {current_branch}"
    ]

    for cmd in git_commands:
        if not run_step(cmd, is_git=True):
            print("\n⚠️ GITHUB SYNC FAILED: Local reports are saved, but cloud upload failed.")
            break

    total_duration = round((time.time() - start_time) / 60, 2)
    
    print(f"\n{'⭐'*30}")
    print(f"✨ PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"⏱️ Total Execution Time: {total_duration} minutes")
    print(f"🔗 Repository: https://github.com/iliamgeladze1998/music-store-scraper")
    print(f"📂 Check the latest SMART_REPORT_*.xlsx for results.")
    print(f"{'⭐'*30}")

if __name__ == "__main__":
    main()