import subprocess
import sys
import io
from datetime import datetime

# Fix UTF-8 encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_script_silent(script_name, description):
    """Run a script in autonomous mode with error resilience"""
    print(f"\n{'='*60}")
    print(f"STARTING: {description}")
    print(f"Script: {script_name}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # Run the script with subprocess
        cmd = [sys.executable, script_name]
        print(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=sys.path[0],  # Current directory
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Print output regardless of success/failure
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Check result
        if result.returncode == 0:
            print(f"\nSUCCESS: {description} completed successfully")
            return True
        else:
            print(f"\nERROR: {description} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: Failed to run {script_name}")
        print(f"Exception: {str(e)}")
        return False

def main():
    """Main orchestration function - runs all scrapers autonomously"""
    print("\n" + "="*80)
    print("AUTONOMOUS SCRAPER ORCHESTRATION")
    print("This script will run all scrapers without user input")
    print("Target Google Sheets: Acoustic, Midi, Mireli")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track overall success
    results = {}
    
    # Step 1: Run Music Store & Geovoice comparisons
    print("\n" + "-"*60)
    print("PHASE 1: Music Store & Geovoice Comparisons")
    print("-"*60)
    
    results['run_all_comparisons'] = run_script_silent(
        "run_all_comparisons.py", 
        "Music Store & Geovoice Comparisons (Acoustic + Midi tabs)"
    )
    
    # Step 2: Run Mireli comparison
    print("\n" + "-"*60)
    print("PHASE 2: Mireli Comparison")
    print("-"*60)
    
    results['master_mireli'] = run_script_silent(
        "master_mireli.py", 
        "Mireli Comparison (Mireli tab)"
    )
    
    # Final summary
    print("\n" + "="*80)
    print("AUTONOMOUS SCRAPER ORCHESTRATION COMPLETE")
    print("="*80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nSUMMARY:")
    
    if results['run_all_comparisons']:
        print("✓ Music Store & Geovoice: SUCCESS")
    else:
        print("✗ Music Store & Geovoice: FAILED")
    
    if results['master_mireli']:
        print("✓ Mireli: SUCCESS")
    else:
        print("✗ Mireli: FAILED")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nOverall: {success_count}/{total_count} scripts completed successfully")
    print("Google Sheets targeted:")
    print("- Acoustic tab (via run_all_comparisons.py)")
    print("- Midi tab (via run_all_comparisons.py)")  
    print("- Mireli tab (via master_mireli.py)")
    print("="*80)
    
    # Always exit with 0 since we want to indicate orchestration completed
    # Individual script failures are logged above
    sys.exit(0)

if __name__ == "__main__":
    main()
