import pandas as pd
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_geovoice_comparison():
    """Test Geovoice vs Acoustic price comparison logic."""
    
    logger.info("=== Geovoice Price Comparison Test ===")
    
    # Input files
    geovoice_file = "geovoice_inventory.csv"
    
    # Find most recent acoustic inventory file
    import glob
    acoustic_files = glob.glob("acoustic_inventory_*.xlsx")
    if not acoustic_files:
        logger.error("No acoustic inventory files found!")
        return False
    
    latest_acoustic = max(acoustic_files, key=lambda x: x.split('_')[1] + x.split('_')[2].split('.')[0])
    logger.info(f"Using latest acoustic file: {latest_acoustic}")
    
    try:
        # Load Geovoice data
        logger.info(f"Loading Geovoice: {geovoice_file}")
        geovoice_df = pd.read_csv(geovoice_file)
        logger.info(f"[INPUT AUDIT] Geovoice Unique IDs found: {len(geovoice_df)}")
        
        # Load Acoustic data
        logger.info(f"Loading Acoustic: {latest_acoustic}")
        acoustic_df = pd.read_excel(latest_acoustic)
        logger.info(f"[INPUT AUDIT] Acoustic Unique IDs found: {len(acoustic_df)}")
        
        # Clean column names and data
        geovoice_df.columns = geovoice_df.columns.str.strip()
        acoustic_df.columns = acoustic_df.columns.str.strip()
        
        # Clean UNIQUE_ID columns and debug formats
        geovoice_df['UNIQUE_ID'] = geovoice_df['UNIQUE_ID'].astype(str).str.strip()
        acoustic_df['UNIQUE_ID'] = acoustic_df['UNIQUE_ID'].astype(str).str.strip()
        
        # Debug: Show ID formats
        logger.info(f"[DEBUG] Geovoice ID formats: {list(geovoice_df['UNIQUE_ID'].head())}")
        logger.info(f"[DEBUG] Acoustic ID formats: {list(acoustic_df['UNIQUE_ID'].head())}")
        
        # Show more examples for comparison
        logger.info(f"[DEBUG] More Geovoice IDs: {list(geovoice_df['UNIQUE_ID'].head(10))}")
        logger.info(f"[DEBUG] More Acoustic IDs: {list(acoustic_df['UNIQUE_ID'].head(10))}")
        
        # Show sample data
        logger.info(f"[FORMAT SAMPLE] First 5 Geovoice IDs: {list(geovoice_df['UNIQUE_ID'].head())}")
        logger.info(f"[FORMAT SAMPLE] First 5 Acoustic IDs: {list(acoustic_df['UNIQUE_ID'].head())}")
        
        # Merge on UNIQUE_ID
        logger.info("[MATCHING] Merging datasets...")
        merged_df = pd.merge(
            geovoice_df,
            acoustic_df,
            on='UNIQUE_ID',
            how='inner',
            suffixes=('_GEO', '_AC')
        )
        
        logger.info(f"[MATCHING] Final matches identified: {len(merged_df)}")
        
        if len(merged_df) == 0:
            logger.warning("No matches found! This might indicate ID format issues.")
            return False
        
        # Calculate price difference: PRICE_GEO - PRICE_AC
        logger.info("[CALCULATION] Computing price differences...")
        merged_df['Price_Diff'] = merged_df['Price'] - merged_df['PRICE']  # Geovoice Price - Acoustic Price
        
        # Create final report with exact Music Store structure including both links
        final_report = merged_df[[
            'UNIQUE_ID',
            'NAME',  # Acoustic name -> will become Product_Name
            'PRICE',  # Acoustic price -> will become Price_Acoustic
            'Price',  # Geovoice price -> will become Price_Geovoice
            'STATUS',  # Acoustic status -> will become Status_Acoustic
            'Status',  # Geovoice status -> will become Status_Geovoice
            'LINK',  # Acoustic link -> will become Link_Acoustic
            'Link',  # Geovoice link -> will become Link_Geovoice
            'Price_Diff'
        ]].copy()
        
        # Rename columns to match Music Store structure exactly
        final_report = final_report.rename(columns={
            'UNIQUE_ID': 'UNIQUE_ID',
            'NAME': 'Product_Name',
            'PRICE': 'Price_Acoustic',
            'Price': 'Price_Geovoice',
            'STATUS': 'Status_Acoustic',
            'Status': 'Status_Geovoice',
            'LINK': 'Link_Acoustic',
            'Link': 'Link_Geovoice',
            'Price_Diff': 'Price_Diff'
        })
        
        # Reorder columns to exact Music Store structure
        final_report = final_report[[
            'UNIQUE_ID',
            'Product_Name',
            'Price_Acoustic',
            'Price_Geovoice',
            'Price_Diff',
            'Status_Acoustic',
            'Status_Geovoice',
            'Link_Acoustic',
            'Link_Geovoice'
        ]]
        
        # Sort by Price_Diff (ascending - cheapest Geovoice first)
        final_report = final_report.sort_values('Price_Diff', ascending=True)
        
        # Save test report
        output_file = "TEST_GEOVOICE_REPORT.xlsx"
        final_report.to_excel(output_file, index=False)
        
        # Print summary
        logger.info(f"\n=== COMPARISON SUMMARY ===")
        logger.info(f"Total products in Geovoice: {len(geovoice_df)}")
        logger.info(f"Total products in Acoustic: {len(acoustic_df)}")
        logger.info(f"Matches found: {len(merged_df)}")
        logger.info(f"Price difference range: {final_report['Price_Diff'].min()} to {final_report['Price_Diff'].max()}")
        logger.info(f"Test report saved: {output_file}")
        
        # Show sample matches
        logger.info(f"\n=== SAMPLE MATCHES ===")
        for i, row in final_report.head(3).iterrows():
            logger.info(f"ID: {row['UNIQUE_ID']} | GEO: {row['Price_Geovoice']} | AC: {row['Price_Acoustic']} | Diff: {row['Price_Diff']}")
        
        logger.info("\n✅ Structure standardized. Ready for visual inspection.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in comparison test: {e}")
        return False

if __name__ == "__main__":
    success = test_geovoice_comparison()
    if success:
        logger.info("✅ Geovoice comparison test completed successfully!")
    else:
        logger.error("❌ Geovoice comparison test failed!")
    sys.exit(0 if success else 1)
