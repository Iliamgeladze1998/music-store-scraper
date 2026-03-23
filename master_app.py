import subprocess
import sys
import time
from datetime import datetime

def run_step(script_name, is_git=False):
    """Executes a python script or a Git command"""
    print(f"\n{'='*50}")
    print(f"🚀 {'Git Operation' if is_git else 'Process Started'}: {script_name}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        if is_git:
            # Using shell=True for Git commands
            process = subprocess.run(script_name, shell=True, check=True)
        else:
            # Executing Python scripts
            process = subprocess.run([sys.executable, script_name], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error occurred in {script_name}!")
        return False

def main():
    start_all = time.time()
    
    # 📝 1. Scanning and Comparison steps
    scripts = [
        "get_links.py",          # Acoustic Links Collector
        "geovoice_get_links.py",  # Geovoice Links Collector
        "scraper.py",            # Acoustic Scraper
        "crawler.py",            # Geovoice Scraper
        "compare_prices.py"      # Price Comparison Engine
    ]
    
    for script in scripts:
        if not run_step(script):
            print(f"🛑 Execution halted due to error in: {script}")
            sys.exit(1)

    # 📝 2. Automatic GitHub Upload
    print("\n☁️ Starting automated GitHub upload...")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    git_commands = [
        "git add .",
        f'git commit -m "Auto-update: Market Analysis {timestamp}"',
        "git push origin main"
    ]

    for cmd in git_commands:
        if not run_step(cmd, is_git=True):
            print("⚠️ GitHub upload failed, but local scripts completed successfully.")
            break

    end_all = time.time()
    duration = round((end_all - start_all) / 60, 1)
    
    print(f"\n{'⭐'*20}")
    print(f"🎉 Everything is ready!")
    print(f"⏱️ Total duration: {duration} minutes")
    print(f"🔗 View on GitHub: https://github.com/iliamgeladze1998/music-store-scraper")
    print(f"{'⭐'*20}")

if __name__ == "__main__":
    main()