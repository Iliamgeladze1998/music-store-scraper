import subprocess
import sys
import io
from datetime import datetime

# Fix UTF-8 encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_script_realtime(script_name, description):
    """Run a script and show real-time output without capturing"""
    print(f"\n{'='*60}")
    print(f"STARTING: {description}")
    print(f"Script: {script_name}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # Run the script with real-time output (no capture)
        cmd = [sys.executable, script_name]
        print(f"Executing: {' '.join(cmd)}")
        print("-" * 40)
        
        result = subprocess.run(
            cmd,
            cwd=sys.path[0],  # Current directory
            text=True,
            encoding='utf-8'
            # NO capture_output=True - shows real-time output
        )
        
        print("-" * 40)
        
        # Check result but don't stop execution
        if result.returncode == 0:
            print(f"SUCCESS: {description} completed (exit code 0)")
            return True
        else:
            print(f"WARNING: {description} finished with exit code {result.returncode}")
            print("Continuing to next phase...")
            return False
            
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to run {script_name}")
        print(f"Exception: {str(e)}")
        print("Continuing to next phase...")
        return False

def main():
    """Simple orchestrator - runs scripts sequentially with real-time output"""
    print("\n" + "="*80)
    print("SIMPLE SCRAPER ORCHESTRATOR")
    print("Real-time output mode - showing script progress as it happens")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Phase 1: Music Store & Geovoice
    print("\n" + "-"*60)
    print("PHASE 1: Music Store & Geovoice Comparisons")
    print("This will update Acoustic and Midi Google Sheet tabs")
    print("-"*60)
    
    phase1_success = run_script_realtime(
        "proc_compare_by_id.py", 
        "Music Store & Geovoice Comparisons"
    )
    
    # Phase 2: Mireli
    print("\n" + "-"*60)
    print("PHASE 2: Mireli Comparison")
    print("This will update Mireli Google Sheet tab")
    print("-"*60)
    
    phase2_success = run_script_realtime(
        "store_mireli_master.py", 
        "Mireli Comparison"
    )
    
    # Final summary
    print("\n" + "="*80)
    print("ORCHESTRATION COMPLETE")
    print("="*80)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\nPHASE SUMMARY:")
    if phase1_success:
        print("✓ Phase 1 (Music Store & Geovoice): SUCCESS")
    else:
        print("✗ Phase 1 (Music Store & Geovoice): Issues detected")
    
    if phase2_success:
        print("✓ Phase 2 (Mireli): SUCCESS")
    else:
        print("✗ Phase 2 (Mireli): Issues detected")
    
    print("\nGoogle Sheets targeted:")
    print("- Acoustic tab (via proc_compare_by_id.py)")
    print("- Midi tab (via proc_compare_by_id.py)")
    print("- Mireli tab (via store_mireli_master.py)")
    print("="*80)
    
    # Always exit with 0 - orchestrator completed its job
    sys.exit(0)

if __name__ == "__main__":
    main()
