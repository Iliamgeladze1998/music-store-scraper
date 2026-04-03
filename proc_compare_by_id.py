import subprocess
import sys
import logging
from datetime import datetime
import os

# Store-Agnostic Configuration
BASE_STORE = "acoustic"  # Can be changed to "musicroom", "mireli", etc.
BASE_STORE_FILE = f"{BASE_STORE}_inventory.xlsx"  # Base store inventory file
COMPARISON_STORES = ["music_store", "geovoice"]  # Stores to compare against base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/proc_compare_by_id.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name, description):
    """Run a Python script and return success status."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting: {description}")
    logger.info(f"Executing: {script_name}")
    logger.info(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False,
            text=True,
            timeout=7200  # 2 hours timeout
        )
        logger.info(f"SUCCESS: {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR in {description}: Exit code {e.returncode}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: {description} exceeded 2 hours")
        return False
    except Exception as e:
        logger.error(f"FATAL ERROR in {description}: {e}")
        return False

def main():
    """Main execution for running ID-based comparisons against base store."""
    
    logger.info("\n" + "="*80)
    logger.info("ID-BASED PRICE COMPARISON RUNNER")
    logger.info(f"Base Store: {BASE_STORE.upper()}")
    logger.info(f"Comparison Stores: {', '.join([s.upper() for s in COMPARISON_STORES])}")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    results = {}
    
    # Run comparisons for each store
    for store in COMPARISON_STORES:
        logger.info(f"\n{store.upper()} Comparison ====================")
        script_name = f"store_{store}_master.py"
        description = f"{store.title()} Comparison Workflow"
        
        results[store] = run_script(script_name, description)
        
        if results[store]:
            logger.info(f"{store.title()} comparison completed successfully!")
        else:
            logger.error(f"{store.title()} comparison failed!")
    
    # Final Summary
    logger.info("\n" + "="*80)
    logger.info("FINAL EXECUTION SUMMARY:")
    
    for store in COMPARISON_STORES:
        status = 'SUCCESS' if results[store] else 'FAILED'
        store_name = store.replace('_', ' ').title()
        logger.info(f"   {store_name}: {status}")
    
    overall_success = all(results.values())
    
    if overall_success:
        logger.info("\nOVERALL RESULT: ALL COMPARISONS COMPLETED SUCCESSFULLY!")
        logger.info(f"All comparison tabs have been updated in Google Sheets")
    else:
        logger.info("\nOVERALL RESULT: SOME COMPARISONS FAILED")
        logger.info("Please check the logs above for details")
    
    logger.info(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80 + "\n")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: {e}", exc_info=True)
        sys.exit(1)
