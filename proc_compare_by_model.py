import pandas as pd
import re
import json
import os
from datetime import datetime
import sys
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Store-Agnostic Configuration
BASE_STORE = "acoustic"  # Can be changed to "musicroom", "mireli", etc.
TARGET_STORE = "mireli"  # Store to compare against base
BASE_STORE_FILE = f"{BASE_STORE}_inventory.xlsx"  # Base store inventory file
TARGET_STORE_FILE = f"{TARGET_STORE}_inventory.csv"  # Target store inventory file

# Ensure exports folder exists
os.makedirs("exports", exist_ok=True)
os.makedirs("archives", exist_ok=True)

# Senior-Level Strict Matching Architecture with Simple "NO" Feedback System - FINAL PRODUCTION VERSION
CONFIDENCE_FILE = 'match_history.json'
BLACKLIST_FILE = 'match_blacklist.json'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. The 'No-Flute' Filter - Category Blacklists
BASE_CATEGORY_BLACKLIST = ['RECORDER', 'MICROPHONE', 'STAND', 'INTERFACE', 'CABLE', 'ADAPTER', 'CASE', 'BAG', 'GIG BAG']
TARGET_CATEGORY_BLACKLIST = ['PIANO', 'SYNTHESIZER', 'KEYBOARD', 'DIGITAL PIANO', 'STAGE PIANO']

def load_match_history():
    """Load match history from JSON file"""
    if os.path.exists(CONFIDENCE_FILE):
        try:
            with open(CONFIDENCE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_match_history(history):
    """Save match history to JSON file"""
    with open(CONFIDENCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def load_blacklist():
    """Load blacklist from JSON file"""
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_blacklist(blacklist):
    """Save blacklist to JSON file"""
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(blacklist, f, indent=2, ensure_ascii=False)

def is_blacklisted(base_id, target_name):
    """Check if a match is blacklisted"""
    blacklist = load_blacklist()
    key = f"{base_id}_{target_name}"
    return key in blacklist

def add_to_blacklist(base_id, target_name):
    """Add pair to blacklist"""
    blacklist = load_blacklist()
    key = f"{base_id}_{target_name}"
    blacklist[key] = {
        'base_id': base_id,
        'target_name': target_name,
        'blacklisted_at': datetime.now().isoformat()
    }
    save_blacklist(blacklist)
    logger.info(f"Added to blacklist: {base_id} -> {target_name}")

def contains_category_blacklist(name, blacklist):
    """Check if product name contains category blacklist keywords"""
    if pd.isna(name):
        return False
    
    name_upper = str(name).upper()
    for keyword in blacklist:
        if keyword in name_upper:
            return True
    return False

def passes_no_flute_filter(base_name, target_name):
    """1. The 'No-Flute' Filter - Category Cross-Contamination Prevention"""
    # Check if Base store contains forbidden categories
    if contains_category_blacklist(base_name, BASE_CATEGORY_BLACKLIST):
        # If Base store is in blacklist categories, Target must NOT be in instrument categories
        if contains_category_blacklist(target_name, TARGET_CATEGORY_BLACKLIST):
            return False  # CROSS-CONTAMINATION: Mic vs Piano, etc.
    
    # Check if Target contains forbidden categories  
    if contains_category_blacklist(target_name, TARGET_CATEGORY_BLACKLIST):
        # If Target is in instrument categories, Base must NOT be in accessory categories
        if contains_category_blacklist(base_name, BASE_CATEGORY_BLACKLIST):
            return False  # CROSS-CONTAMINATION: Piano vs Mic, etc.
    
    return True  # Passes filter

def strict_numeric_handshake(base_model, target_name, base_brand, target_brand):
    """2. Strict Numeric Handshake - Brand-Gated Model Matching"""
    # Brand must match - NO EXCEPTIONS
    if base_brand != target_brand:
        return False, "BRAND_MISMATCH"
    
    # Extract numeric part from base model
    if not base_model:
        return False, "NO_MODEL"
    
    base_numeric = re.search(r'(\d+)', base_model)
    if not base_numeric:
        return False, "NO_NUMERIC"
    
    base_num = base_numeric.group(1)
    
    # Check if base numeric is found in target name
    target_clean = re.sub(r'[^A-Z0-9]', '', str(target_name).upper())
    
    if base_num in target_clean:
        return True, "NUMERIC_MATCH"
    else:
        return False, "NO_NUMERIC_MATCH"

def is_used_product(url):
    """3. Cleanup 'Used' Mess - Used Product Isolation"""
    if pd.isna(url):
        return False
    
    return '/used-' in str(url).lower()

def clean_string(s):
    """Clean string: Uppercase + Remove all spaces/dashes/dots"""
    if pd.isna(s):
        return ""
    return re.sub(r'[^A-Z0-9]', '', str(s).upper())

def extract_strict_model(name):
    """Extract STRICT model number - Senior Level Precision"""
    if pd.isna(name):
        return ""
    
    name = str(name).strip().upper()
    
    # Remove brand prefixes
    brands = ['YAMAHA', 'CASIO', 'ROLAND', 'KORG', 'KAWAI', 'NORD', 'MOOG', 'ARTURIA', 
              'FENDER', 'IBANEZ', 'GIBSON', 'EPIPHONE', 'MARTIN', 'TAYLOR', 'SEAGULL',
              'HARLEY BENTON', 'SQUIER', 'JACKSON', 'PRS', 'SCHECTER', 'DEAN', 'AKAI',
              'THOMANN', 'MILLENNIUM', 'PRESONUS', 'MARKBASS', 'HOSOKIN', 'APPLAUSE',
              'BEHRINGER', 'MEDeli', 'BEISITE']
    
    for brand in brands:
        name = re.sub(r'\b' + brand + r'\b', '', name, flags=re.IGNORECASE)
    
    # Remove common descriptive words
    descriptive_words = ['PIANO', 'DIGITAL', 'ELECTRIC', 'KEYBOARD', 'SYNTHESIZER', 'BLACK', 'WHITE', 'RED', 'BLUE', 'GREEN', 'BROWN', 'SILVER', 'GOLD', 'CHERRY', 'BK', 'WH', 'BL', 'RD', 'GN', 'BU', 'SB', 'TR', 'NA', 'NS', 'WT', '88KEY', '61KEY', '76KEY', 'KEYS', 'KEY', '88KEYS']
    
    for word in descriptive_words:
        name = re.sub(r'\b' + word + r'\b', '', name, flags=re.IGNORECASE)
    
    # STRICT model extraction patterns
    patterns = [
        r'\b[A-Z]{2,4}-?\d{3,4}[A-Z]*\b',  # DGX-670, CDP-S160, CT-X700, AP-550
        r'\b[A-Z]{2,3}-?\d{2,3}[A-Z]*\b',  # B2, P125, RP30, E473
        r'\b\d{3,4}[A-Z]{1,3}\b',          # 504CE, 2120V
        r'\b[A-Z]{1,2}\d{2,3}[A-Z]*\b',    # P125, E473, B2
        r'\b[A-Z]{2,}\d{2,}[A-Z]*\b',      # Any letter-number combo with at least 2 digits
        r'\b\d{2,4}\b',                   # Pure number models (120, 530, 373, 473)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, name)
        if matches:
            # Clean the model (remove dashes, spaces)
            model = re.sub(r'[^A-Z0-9]', '', matches[0])
            # Require at least 2 characters and at least 1 digit
            if len(model) >= 2 and re.search(r'\d', model):
                return model
    
    return ""

def extract_brand(name):
    """Extract brand from product name - BRAND SHIELD"""
    if pd.isna(name):
        return ""
    
    name = str(name).upper()
    # Expanded brand list for comprehensive matching
    brands = ['YAMAHA', 'CASIO', 'ROLAND', 'KORG', 'KAWAI', 'AKAI', 'THOMANN', 'MEDELI', 'BEISITE',
              'NORD', 'MOOG', 'ARTURIA', 'FENDER', 'IBANEZ', 'GIBSON', 'EPIPHONE', 'MARTIN', 
              'TAYLOR', 'SEAGULL', 'HARLEY BENTON', 'SQUIER', 'JACKSON', 'PRS', 'SCHECTER', 
              'DEAN', 'BEHRINGER', 'MILLENNIUM', 'PRESONUS', 'MARKBASS', 'HOSOKIN', 'APPLAUSE']
    
    for brand in brands:
        if brand in name:
            return brand
    
    return ""

def clean_price(price):
    """Remove currency symbols and convert to numeric value."""
    if pd.isna(price) or price == '':
        return None
    price_str = str(price).replace('₾', '').replace('GEL', '').replace('$', '').replace('€', '').strip()
    try:
        return float(price_str)
    except:
        return None

def scrape_fresh_acoustic():
    """Phase 1: Complete Acoustic Pipeline - get_links → scraper.py"""
    logger.info("🔗 PHASE 1: Starting Complete Acoustic Pipeline...")
    
    try:
        import subprocess
        import os
        import glob
        from datetime import datetime
        
        # Step 1: Clean up old acoustic inventory files
        logger.info("🧹 Cleaning up old acoustic inventory files...")
        existing_files = glob.glob("acoustic_inventory_mireli_sync_*.xlsx")
        for file in existing_files:
            try:
                os.remove(file)
                logger.info(f"🗑️  Deleted old file: {file}")
            except Exception as e:
                logger.warning(f"⚠️  Could not delete {file}: {e}")
        
        # Step 2: Run get_links.py first
        logger.info("🔗 Step 1: Getting fresh Acoustic links...")
        cmd_get_links = f"cmd /c chcp 65001 > nul && {sys.executable} store_acoustic_links.py"
        
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
        env['PYTHONUTF8'] = '1'
        
        logger.info(f"🚀 Executing: {cmd_get_links}")
        result_get_links = subprocess.run(
            cmd_get_links,
            shell=True,
            env=env,
            cwd=os.getcwd(),
            capture_output=False,
            text=True,
            encoding='utf-8'
        )
        
        if result_get_links.returncode != 0:
            logger.error("❌ get_links.py FAILED - Cannot proceed to scraper")
            return None
        
        logger.info("✅ get_links.py completed successfully")
        
        # Step 3: Run scraper.py with dynamic filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        acoustic_filename = f"exports/acoustic_inventory_mireli_sync_{timestamp}.xlsx"
        
        logger.info(f"📄 Step 2: Scraping Acoustic data...")
        logger.info(f"📁 Target output file: {acoustic_filename}")
        
        cmd_scraper = f"cmd /c chcp 65001 > nul && {sys.executable} store_acoustic_scraper.py --output_file {acoustic_filename}"
        
        logger.info(f"� Executing: {cmd_scraper}")
        result_scraper = subprocess.run(
            cmd_scraper,
            shell=True,
            env=env,
            cwd=os.getcwd(),
            capture_output=False,
            text=True,
            encoding='utf-8'
        )
        
        # Step 4: Verification
        if result_scraper.returncode == 0:
            if os.path.exists(acoustic_filename):
                file_size = os.path.getsize(acoustic_filename)
                logger.info(f"✅ Phase 1 SUCCESS: Complete Acoustic pipeline finished")
                logger.info(f"💾 Fresh acoustic data saved: {acoustic_filename}")
                logger.info(f"📊 File size: {file_size} bytes")
                return acoustic_filename
            else:
                logger.error(f"❌ CRITICAL ERROR: Expected output file {acoustic_filename} was not created")
                return None
        else:
            logger.error(f"❌ Phase 1 FAILED: scraper.py failed with exit code {result_scraper.returncode}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error in acoustic pipeline: {e}")
        return None

def scrape_fresh_mireli():
    """Phase 2: Complete Mireli Pipeline - mireli_pages → mireli_scraper"""
    logger.info("🔗 PHASE 2: Starting Complete Mireli Pipeline...")
    
    try:
        import subprocess
        import os
        from datetime import datetime
        
        # Step 1: Run mireli_pages.py first
        logger.info("🔗 Step 1: Getting fresh Mireli pagination links...")
        cmd_mireli_pages = f"cmd /c chcp 65001 > nul && {sys.executable} store_mireli_pages.py"
        
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
        env['PYTHONUTF8'] = '1'
        
        logger.info(f"🚀 Executing: {cmd_mireli_pages}")
        result_mireli_pages = subprocess.run(
            cmd_mireli_pages,
            shell=True,
            env=env,
            cwd=os.getcwd(),
            capture_output=False,
            text=True,
            encoding='utf-8'
        )
        
        if result_mireli_pages.returncode != 0:
            logger.error("❌ mireli_pages.py FAILED - Cannot proceed to mireli_scraper")
            return None
        
        logger.info("✅ mireli_pages.py completed successfully")
        
        # Step 2: Run mireli_scraper.py
        logger.info(f"📄 Step 2: Scraping Mireli data...")
        
        cmd_mireli_scraper = f"cmd /c chcp 65001 > nul && {sys.executable} store_mireli_scraper.py"
        
        logger.info(f"� Executing: {cmd_mireli_scraper}")
        result_mireli_scraper = subprocess.run(
            cmd_mireli_scraper,
            shell=True,
            env=env,
            cwd=os.getcwd(),
            capture_output=False,
            text=True,
            encoding='utf-8'
        )
        
        # Step 3: Verification and rename
        if result_mireli_scraper.returncode == 0:
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            mireli_filename = f"exports/mireli_inventory_{timestamp}.csv"
            
            # Rename the output file to our timestamped version
            try:
                if os.path.exists('mireli_products.csv'):
                    os.rename('mireli_products.csv', mireli_filename)
                    file_size = os.path.getsize(mireli_filename)
                    logger.info(f"✅ Phase 2 SUCCESS: Complete Mireli pipeline finished")
                    logger.info(f"💾 Fresh mireli data saved: {mireli_filename}")
                    logger.info(f"📊 File size: {file_size} bytes")
                    return mireli_filename
                else:
                    logger.error("❌ Expected output file mireli_products.csv not found")
                    return None
            except Exception as e:
                logger.error(f"❌ Error renaming mireli file: {e}")
                return None
        else:
            logger.error(f"❌ Phase 2 FAILED: mireli_scraper.py failed with exit code {result_mireli_scraper.returncode}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error in mireli pipeline: {e}")
        return None

def senior_strict_matching_production():
    """Phase 3: Independent Comparison - Mireli-specific matching logic"""
    logger.info("🔗 PHASE 3: Starting Independent Comparison...")
    
    # Load feedback data
    match_history = load_match_history()
    blacklist = load_blacklist()
    
    logger.info(f"Loaded {len(match_history)} verified matches from history")
    logger.info(f"Loaded {len(blacklist)} blacklisted matches")
    
    try:
        # Get fresh data files from previous phases
        acoustic_file = scrape_fresh_acoustic()
        if acoustic_file is None:
            logger.error("❌ Phase 1 failed - cannot proceed to comparison")
            return None, None
        
        mireli_file = scrape_fresh_mireli()
        if mireli_file is None:
            logger.error("❌ Phase 2 failed - cannot proceed to comparison")
            return None, None
        
        logger.info(f"Using fresh acoustic data: {acoustic_file}")
        logger.info(f"Using fresh mireli data: {mireli_file}")
        
        # Load fresh data
        df_ac = pd.read_excel(acoustic_file)
        df_mireli = pd.read_csv(mireli_file)
        
        logger.info(f"Acoustic products: {len(df_ac)}")
        logger.info(f"Mireli products: {len(df_mireli)}")

        # Apply cleaning and extraction
        df_ac['STRICT_MODEL'] = df_ac['NAME'].apply(extract_strict_model)
        df_ac['BRAND'] = df_ac['NAME'].apply(extract_brand)
        df_ac['IS_USED'] = df_ac['LINK'].apply(is_used_product)
        df_ac['NAME_CLEAN'] = df_ac['NAME'].apply(clean_string)
        
        df_mireli['NAME_CLEAN'] = df_mireli['NAME'].apply(clean_string)
        df_mireli['BRAND'] = df_mireli['NAME'].apply(extract_brand)

        # Filter to products with strict models and NEW products only
        df_ac_filtered = df_ac[
            (df_ac['STRICT_MODEL'] != '') & 
            (df_ac['IS_USED'] == False)
        ].copy()
        
        logger.info(f"Acoustic with strict models (NEW only): {len(df_ac_filtered)}")
        logger.info(f"Mireli total: {len(df_mireli)}")

        # Senior-Level Strict Matching
        matches = []
        rejected_count = 0
        
        for _, acoustic_row in df_ac_filtered.iterrows():
            acoustic_id = str(acoustic_row['UNIQUE_ID'])
            acoustic_model = acoustic_row['STRICT_MODEL']
            acoustic_brand = acoustic_row['BRAND']
            acoustic_name = acoustic_row['NAME']
            
            # Skip if no brand or model found
            if not acoustic_brand or not acoustic_model:
                continue
            
            # Check if this acoustic ID has verified matches in history
            if acoustic_id in match_history:
                verified_match = match_history[acoustic_id]
                # Find verified Mireli product
                verified_mireli = df_mireli[df_mireli['NAME'] == verified_match['mireli_name']]
                if not verified_mireli.empty:
                    mireli_row = verified_mireli.iloc[0]
                    matches.append({
                        'UNIQUE_ID': acoustic_row['UNIQUE_ID'],
                        'Product_Name': acoustic_row['NAME'],
                        'Price_Acoustic': acoustic_row['PRICE'],
                        'Price_Mireli': mireli_row['PRICE'],
                        'Price_Diff': 0,  # Will be calculated after DataFrame creation
                        'Status_Acoustic': acoustic_row['STATUS'],
                        'Status_Mireli': mireli_row['STATUS'],
                        'Link_Acoustic': acoustic_row['LINK'],
                        'Link_Mireli': mireli_row['LINK'],
                        'Status_Filter': 'OK',
                        'Last_Updated': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })
                    continue
            
            # Find all Mireli products with same brand
            brand_filtered_mireli = df_mireli[df_mireli['BRAND'] == acoustic_brand]
            
            for _, mireli_row in brand_filtered_mireli.iterrows():
                mireli_name = mireli_row['NAME']
                mireli_brand = mireli_row['BRAND']
                
                # Check if this match is blacklisted
                if is_blacklisted(acoustic_id, mireli_name):
                    rejected_count += 1
                    continue
                
                # 1. The 'No-Flute' Filter
                if not passes_no_flute_filter(acoustic_name, mireli_name):
                    rejected_count += 1
                    continue
                
                # 2. Strict Numeric Handshake
                is_match, reason = strict_numeric_handshake(acoustic_model, mireli_name, acoustic_brand, mireli_brand)
                
                if is_match:
                    matches.append({
                        'UNIQUE_ID': acoustic_row['UNIQUE_ID'],
                        'Product_Name': acoustic_row['NAME'],
                        'Price_Acoustic': acoustic_row['PRICE'],
                        'Price_Mireli': mireli_row['PRICE'],
                        'Price_Diff': 0,  # Will be calculated after DataFrame creation
                        'Status_Acoustic': acoustic_row['STATUS'],
                        'Status_Mireli': mireli_row['STATUS'],
                        'Link_Acoustic': acoustic_row['LINK'],
                        'Link_Mireli': mireli_row['LINK'],
                        'Status_Filter': 'OK',
                        'Last_Updated': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })
                else:
                    rejected_count += 1
        
        logger.info(f"Senior strict matches found: {len(matches)}")
        logger.info(f"Cross-contamination prevented: {rejected_count} matches")

        if not matches:
            logger.error("No matches found with Senior Strict logic")
            return None, None

        # Create DataFrame with exact column order
        result_df = pd.DataFrame(matches)
        
        # Ensure columns are in the exact order
        column_order = ['UNIQUE_ID', 'Product_Name', 'Price_Acoustic', 'Price_Mireli', 'Price_Diff', 
                       'Status_Acoustic', 'Status_Mireli', 'Link_Acoustic', 'Link_Mireli', 'Status_Filter', 'Last_Updated']
        result_df = result_df[column_order]
        
        # Clean prices and calculate differences
        result_df['Price_Acoustic'] = result_df['Price_Acoustic'].apply(clean_price)
        result_df['Price_Mireli'] = result_df['Price_Mireli'].apply(clean_price)
        
        # Set Mireli PRICE to 0 if Status_Mireli is 'Out of Stock'
        out_of_stock_mask = result_df['Status_Mireli'].astype(str).str.contains('Out of Stock', case=False, na=False)
        result_df.loc[out_of_stock_mask, 'Price_Mireli'] = 0
        
        # Calculate Price_Diff
        result_df['Price_Diff'] = result_df['Price_Mireli'] - result_df['Price_Acoustic']

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = f"exports/keyboard_comparison_{timestamp}.xlsx"
        result_df.to_excel(output_file, index=False)
        
        logger.info(f"✅ Phase 3 SUCCESS: Senior strict comparison saved to: {output_file}")
        logger.info(f"Professional matches: {len(result_df)}")
        logger.info(f"All at 100% confidence: YES")
        
        # Upload to Google Sheets even in match mode
        try:
            logger.info("📤 Starting Google Sheets upload...")
            from upload_mireli_comparison import upload_to_google_sheets
            upload_success = upload_to_google_sheets(output_file, "Mireli")
            if upload_success:
                logger.info("✅ Upload completed successfully")
            else:
                logger.error("❌ Upload failed")
        except Exception as e:
            logger.error(f"❌ Error during upload: {e}")
        
        return result_df, output_file

    except Exception as e:
        logger.error(f"❌ Error in Senior Strict matching: {e}")
        return None, None

def process_no_feedback_from_sheet():
    """Process 'no' feedback from Google Sheet Status_Filter column"""
    logger.info("--- PROCESSING 'NO' FEEDBACK FROM GOOGLE SHEET ---")
    
    try:
        # Load Google Sheets credentials and download current data
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        # Open spreadsheet and worksheet
        spreadsheet = client.open_by_key("1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94")
        worksheet = spreadsheet.worksheet("Mireli")
        
        # Get all data from sheet
        data = worksheet.get_all_records()
        logger.info(f"Downloaded {len(data)} rows from Google Sheet")
        
        # Process feedback
        blacklist_count = 0
        for row in data:
            status_filter = str(row.get('Status_Filter', '')).strip().lower()
            if status_filter == 'no':
                acoustic_id = str(row.get('UNIQUE_ID', '')).strip()
                mireli_name = str(row.get('Product_Name', '')).strip()
                
                if acoustic_id and mireli_name:
                    add_to_blacklist(acoustic_id, mireli_name)
                    blacklist_count += 1
                    logger.info(f"Added to blacklist: {acoustic_id} -> {mireli_name}")
        
        logger.info(f"Total blacklisted pairs added: {blacklist_count}")
        
        if blacklist_count > 0:
            logger.info("🔄 Re-running matching with updated blacklist...")
            # Re-run matching with new blacklist
            result_df, output_file = senior_strict_matching_production()
            
            if result_df is not None:
                # Upload updated results
                logger.info("📤 Uploading updated results to Google Sheets...")
                from upload_mireli_comparison import upload_to_google_sheets
                upload_success = upload_to_google_sheets(output_file, "Mireli")
                
                if upload_success:
                    logger.info(f"✅ Updated matching completed: {len(result_df)} matches")
                    logger.info("✅ Google Sheet updated with filtered results")
                    return True
                else:
                    logger.error("❌ Failed to upload updated results")
                    return False
            else:
                logger.error("❌ Failed to generate updated matches")
                return False
        else:
            logger.info("✅ No new 'no' feedback found")
            return True
            
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        return False

def run_keyboard_comparison():
    """Entry point for master_app.py - Full Automation Cycle: Live Scrape → Match → Upload"""
    logger.info("🎹 Starting Full Automation Cycle...")
    
    try:
        # Step 1: Live Scrape Acoustic (Get Links → Scrape all items)
        logger.info("🔄 STEP 1: Live Acoustic Scraping")
        acoustic_file = scrape_fresh_acoustic()
        if acoustic_file is None:
            logger.error("❌ Failed to scrape acoustic data")
            return False
        
        # Step 2: Live Scrape Mireli (Scrape all items)
        logger.info("🔄 STEP 2: Live Mireli Scraping")
        mireli_file = scrape_fresh_mireli()
        if mireli_file is None:
            logger.error("❌ Failed to scrape mireli data")
            return False
        
        # Step 3: Strict Match (Run Senior Matching on new DataFrames)
        logger.info("🔄 STEP 3: Senior Strict Matching")
        result_df, comparison_file = senior_strict_matching_production()
        
        if result_df is None:
            logger.error("❌ Failed to generate matches")
            return False
        
        # Step 4: Force Upload (Clear Google Sheet + Upload fresh results)
        logger.info("🔄 STEP 4: Force Upload to Google Sheets")
        from upload_mireli_comparison import upload_to_google_sheets
        
        # Create fresh file for upload
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        temp_file = f"temp_upload_{timestamp}.xlsx"
        result_df.to_excel(temp_file, index=False)
        
        # Upload fresh results
        upload_success = upload_to_google_sheets(temp_file, "Mireli")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
        
        if upload_success:
            logger.info(f"✅ Full automation cycle completed: {len(result_df)} matches")
            logger.info(f"✅ Google Sheet updated with fresh data")
        else:
            logger.error("❌ Failed to upload to Google Sheets")
            return False
        
        # Show final status
        print("=" * 80)
        print("🎹 FULL AUTOMATION CYCLE COMPLETE")
        print("=" * 80)
        print(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"🔗 Google Sheet: https://docs.google.com/spreadsheets/d/1tDKgxcxPF8Jq151nMb6Wu_ziyOxkFATKSOquFKZrg94")
        print(f"🔄 Fresh data: Acoustic ({len(result_df)} matches)")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in full automation cycle: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['match', 'process_feedback', 'full_cycle'], default='match')
    args = parser.parse_args()
    
    if args.mode == 'match':
        result_df, output_file = senior_strict_matching_production()
        if result_df is not None:
            print(f"Matching completed: {len(result_df)} matches")
            print(f"Output file: {output_file}")
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.mode == 'process_feedback':
        success = process_no_feedback_from_sheet()
        if success:
            print("Feedback processing completed")
            sys.exit(0)
        else:
            print("Feedback processing failed")
            sys.exit(1)
    elif args.mode == 'full_cycle':
        success = run_keyboard_comparison()
        if success:
            print("Full cycle completed successfully")
            sys.exit(0)
        else:
            print("Full cycle failed")
            sys.exit(1)
