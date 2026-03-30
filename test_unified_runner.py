import subprocess
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run_all_comparisons_test.log"),
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
            timeout=300  # 5 minutes timeout for test
        )
        logger.info(f"✅ SUCCESS: {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ ERROR in {description}: Exit code {e.returncode}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ TIMEOUT: {description} exceeded 5 minutes")
        return False
    except Exception as e:
        logger.error(f"💥 FATAL ERROR in {description}: {e}")
        return False

def main():
    """Test execution for both Music Store and Geovoice uploads using existing data."""
    
    logger.info("\n" + "="*80)
    logger.info("🧪 UNIFIED PRICE COMPARISON TEST RUNNER")
    logger.info("📊 Testing Both Music Store & Geovoice Uploads (Using Existing Data)")
    logger.info(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    results = {}
    
    # Step 1: Music Store Quick Upload Test
    logger.info("\n🎵 === STEP 1: Music Store (Musikis-saxli) Quick Upload Test ===")
    results['music_store'] = run_script("quick_upload.py", "Music Store Quick Upload Test")
    
    if results['music_store']:
        logger.info("🎉 Music Store upload test completed successfully!")
    else:
        logger.error("💥 Music Store upload test failed!")
    
    # Step 2: Geovoice Upload Test  
    logger.info("\n🎧 === STEP 2: Geovoice Upload Test ===")
    results['geovoice'] = run_script("test_sheets_upload.py", "Geovoice Upload Test")
    
    if results['geovoice']:
        logger.info("🎉 Geovoice upload test completed successfully!")
    else:
        logger.error("💥 Geovoice upload test failed!")
    
    # Final Summary
    logger.info("\n" + "="*80)
    logger.info("📋 TEST EXECUTION SUMMARY:")
    logger.info(f"   Music Store (Musikis-saxli): {'✅ SUCCESS' if results['music_store'] else '❌ FAILED'}")
    logger.info(f"   Geovoice: {'✅ SUCCESS' if results['geovoice'] else '❌ FAILED'}")
    
    overall_success = results['music_store'] and results['geovoice']
    
    if overall_success:
        logger.info("\n🎊 OVERALL RESULT: ALL UPLOAD TESTS COMPLETED SUCCESSFULLY!")
        logger.info("📈 Both 'Musikis-saxli' and 'Geovoice' tabs have been updated in Google Sheets")
        logger.info("🔍 Ready for full production runs!")
    else:
        logger.info("\n⚠️  OVERALL RESULT: SOME UPLOAD TESTS FAILED")
        logger.info("🔍 Please check the logs above for details")
    
    logger.info(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80 + "\n")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"💥 CRITICAL ERROR: {e}", exc_info=True)
        sys.exit(1)
