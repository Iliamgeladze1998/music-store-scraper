import subprocess
import os
import glob
import sys
import io
from datetime import datetime

# Fix UTF-8 encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_fresh_comparison():
    """Step 1: Run scraping and matching using subprocess"""
    print("STEP 1: Starting scraping and matching...")
    
    try:
        # Build command
        cmd = [sys.executable, "proc_compare_by_model.py", "--mode", "match"]
        
        # Run subprocess
        print(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Check result
        if result.returncode != 0:
            print(f"ERROR: STEP 1 FAILED: Exit code {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
        
        print("SUCCESS: STEP 1 SUCCESS: Scraping and matching completed")
        print(f"Output: {result.stdout}")
        return True
        
    except Exception as e:
        print(f"ERROR: STEP 1 ERROR: {e}")
        return False

def find_latest_comparison_file():
    """Step 2: Find the latest keyboard_comparison_*.xlsx file"""
    print("STEP 2: Finding latest comparison file...")
    
    try:
        # Search for files matching the pattern
        pattern = "exports/keyboard_comparison_*.xlsx"
        files = glob.glob(pattern)
        
        if not files:
            print("ERROR: No keyboard_comparison_*.xlsx files found")
            return None
        
        # Sort by modification time (newest first)
        files.sort(key=os.path.getmtime, reverse=True)
        latest_file = files[0]
        
        print(f"SUCCESS: STEP 2 SUCCESS: Found latest file: {latest_file}")
        print(f"Modified: {datetime.fromtimestamp(os.path.getmtime(latest_file))}")
        return latest_file
        
    except Exception as e:
        print(f"ERROR: STEP 2 ERROR: {e}")
        return None

def upload_comparison_file(file_path):
    """Step 3: Upload the comparison file using subprocess"""
    print("STEP 3: Uploading comparison file...")
    
    try:
        # Build command
        cmd = [sys.executable, "upload_mireli_comparison.py", "--comparison_file", file_path]
        
        # Run subprocess
        print(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Check result
        if result.returncode != 0:
            print(f"ERROR: STEP 3 FAILED: Exit code {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
        
        print("SUCCESS: STEP 3 SUCCESS: Upload completed")
        print(f"Output: {result.stdout}")
        return True
        
    except Exception as e:
        print(f"ERROR: STEP 3 ERROR: {e}")
        return False

def main():
    """Main orchestration function"""
    print("=" * 80)
    print("MASTER MIRELI ORCHESTRATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Scrape & Match
    success = run_fresh_comparison()
    if not success:
        print("\nERROR: ORCHESTRATION FAILED: Step 1 (Scrape & Match) failed")
        print("Stopping execution - will not attempt upload")
        sys.exit(1)
    
    print()
    
    # Step 2: Find latest file
    latest_file = find_latest_comparison_file()
    if latest_file is None:
        print("\nERROR: ORCHESTRATION FAILED: Step 2 (Find file) failed")
        print("No comparison file found to upload")
        sys.exit(1)
    
    print()
    
    # Step 3: Upload
    success = upload_comparison_file(latest_file)
    if not success:
        print("\nERROR: ORCHESTRATION FAILED: Step 3 (Upload) failed")
        sys.exit(1)
    
    # Final success
    print()
    print("=" * 80)
    print("MASTER MIRELI ORCHESTRATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"File uploaded: {latest_file}")
    print(f"Google Sheet: https://docs.google.com/spreadsheets/d/1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94")
    print("=" * 80)

if __name__ == "__main__":
    main()
