import pandas as pd
import os
import glob
import re
from datetime import datetime

def find_latest_file(keyword):
    """ Finds the most recent file, ignoring temporary Excel files (~$) """
    # ვეძებთ ფაილებს, რომლებიც შეიცავენ სახელს და არ იწყებიან ~$ სიმბოლოებით
    files = [f for f in glob.glob(f"*{keyword}*.[cx][ls]*") if not f.startswith("~$")]
    
    if not files:
        return None
    
    latest_file = max(files, key=os.path.getctime)
    print(f"--- Loading: {latest_file} ---")
    
    if latest_file.endswith('.csv'):
        return pd.read_csv(latest_file)
    return pd.read_excel(latest_file)

def clean_id(sku):
    """Removes dashes, dots, and spaces for better matching, always returns a string, and applies .strip().upper()."""
    if pd.isna(sku):
        return ""
    # Remove non-alphanumeric, always string, strip and upper
    return re.sub(r'[^a-zA-Z0-9]', '', str(sku)).strip().upper()

def compare_prices():
    print("--- Starting Price Comparison (Strict ID Matching) ---")

    # 1. მოვძებნოთ ბოლო ფაილები
    df_gv = find_latest_file("geovoice")
    df_ac = find_latest_file("acoustic")

    if df_gv is None or df_ac is None:
        print("❌ Error: Missing inventory files! Make sure scrapers finished correctly.")
        return

    # 2. მოვამზადოთ ID-ები შესადარებლად (გავასუფთაოთ ტირეებისგან)
    df_gv['MATCH_ID'] = df_gv['UNIQUE_ID'].astype(str).apply(lambda x: clean_id(x))
    df_ac['MATCH_ID'] = df_ac['UNIQUE_ID'].astype(str).apply(lambda x: clean_id(x))

    # 3. შევაერთოთ ცხრილები (მხოლოდ ის პროდუქტები, რაც ორივეშია)
    merged_df = pd.merge(
        df_ac, 
        df_gv, 
        on='MATCH_ID', 
        suffixes=('_AC', '_GV')
    )

    if merged_df.empty:
        print("⚠️ No matching products found between the two stores.")
        return

    # 4. ფასების ფორმატირება და სხვაობის დათვლა
    merged_df['PRICE_AC'] = pd.to_numeric(merged_df['PRICE_AC'], errors='coerce').fillna(0)
    merged_df['PRICE_GV'] = pd.to_numeric(merged_df['PRICE_GV'], errors='coerce').fillna(0)
    merged_df['Price_Diff'] = merged_df['PRICE_AC'] - merged_df['PRICE_GV']

    # 5. რეპორტის სვეტების დალაგება
    final_report = merged_df[[
        'UNIQUE_ID_AC',
        'NAME_AC',
        'PRICE_AC',
        'STATUS_AC',
        'NAME_GV',
        'PRICE_GV',
        'STATUS_GV',
        'Price_Diff',
        'LINK_AC',
        'LINK_GV'
    ]].rename(columns={'UNIQUE_ID_AC': 'UNIQUE_ID'})

    # 6. შენახვა
    timestamp = datetime.now().strftime("%m%d_%H%M")
    output_name = f"FINAL_MATCH_REPORT_{timestamp}.xlsx"
    
    final_report.to_excel(output_name, index=False)
    
    print(f"\nSUCCESS!")
    print(f"Matching products found: {len(final_report)}")
    print(f"Report saved as: {output_name}")

if __name__ == "__main__":
    compare_prices()