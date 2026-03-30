import subprocess
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run_all_comparisons.log"),
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
    """Main execution for running both Music Store and Geovoice comparisons."""
    
    logger.info("\n" + "="*80)
    logger.info("UNIFIED PRICE COMPARISON RUNNER")
    logger.info("Running Both Music Store & Geovoice Comparisons")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    results = {}
    
    # Step 1: Music Store Comparison
    logger.info("\nMusic Store Comparison ====================")
    results['music_store'] = run_script("master_app.py", "Music Store Comparison Workflow")
    
    if results['music_store']:
        logger.info("Music Store comparison completed successfully!")
    else:
        logger.error("Music Store comparison failed!")
    
    # Step 2: Geovoice Comparison  
    logger.info("\nGeovoice Comparison ====================")
    results['geovoice'] = run_script("master_geovoice.py", "Geovoice Comparison Workflow")
    
    if results['geovoice']:
        logger.info("Geovoice comparison completed successfully!")
    else:
        logger.error("Geovoice comparison failed!")
    
    # Final Summary
    logger.info("\n" + "="*80)
    logger.info("FINAL EXECUTION SUMMARY:")
    logger.info(f"   Music Store (Musikis-saxli): {'SUCCESS' if results['music_store'] else 'FAILED'}")
    logger.info(f"   Geovoice: {'SUCCESS' if results['geovoice'] else 'FAILED'}")
    
    overall_success = results['music_store'] and results['geovoice']
    
    if overall_success:
        logger.info("\nOVERALL RESULT: ALL COMPARISONS COMPLETED SUCCESSFULLY!")
        logger.info("Both 'Musikis-saxli' and 'Geovoice' tabs have been updated in Google Sheets")
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
