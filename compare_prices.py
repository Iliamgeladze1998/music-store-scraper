
import pandas as pd
import re
from datetime import datetime
import sys

def clean_id(sku):
    """Removes dashes, dots, and spaces for better matching, always returns a string, and applies .strip().upper()."""
    if pd.isna(sku):
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(sku)).strip().upper()

def compare_prices(acoustic_file, musikis_file, output_file):
    print("--- Starting Price Comparison (Strict ID Matching) ---")
    print(f"[INPUT AUDIT] Loading Acoustic: {acoustic_file}", flush=True)
    print(f"[INPUT AUDIT] Loading Musikis Saxli: {musikis_file}", flush=True)
    try:
        df_ac = pd.read_excel(acoustic_file)
        df_ms = pd.read_excel(musikis_file)
    except Exception as e:
        print(f"[ERROR] Failed to load input files: {e}", flush=True)
        return

    print(f"[AUDIT] Musikis Saxli Unique IDs found in Excel: {df_ms['UNIQUE_ID'].nunique()}", flush=True)
    print(f"[AUDIT] Acoustic Unique IDs found in Excel: {df_ac['UNIQUE_ID'].nunique()}", flush=True)
    print(f"[FORMAT SAMPLE] First 5 MS IDs: {df_ms['UNIQUE_ID'].astype(str).head(5).tolist()}", flush=True)
    print(f"[FORMAT SAMPLE] First 5 AC IDs: {df_ac['UNIQUE_ID'].astype(str).head(5).tolist()}", flush=True)

    df_ms['MATCH_ID'] = df_ms['UNIQUE_ID'].astype(str).apply(lambda x: clean_id(x))
    df_ac['MATCH_ID'] = df_ac['UNIQUE_ID'].astype(str).apply(lambda x: clean_id(x))

    merged_df = pd.merge(
        df_ac, 
        df_ms, 
        on='MATCH_ID', 
        suffixes=('_AC', '_MS')
    )

    print(f"[MATCHING] Final matches identified: {len(merged_df)}", flush=True)

    if merged_df.empty:
        print("No matching products found between the two stores.", flush=True)
        return

    merged_df['PRICE_AC'] = pd.to_numeric(merged_df['PRICE_AC'], errors='coerce').fillna(0)
    merged_df['PRICE_MS'] = pd.to_numeric(merged_df['PRICE_MS'], errors='coerce').fillna(0)
    merged_df['Price_Diff'] = merged_df['PRICE_AC'] - merged_df['PRICE_MS']

    final_report = merged_df[[
        'UNIQUE_ID_AC',
        'NAME_AC',
        'PRICE_AC',
        'STATUS_AC',
        'NAME_MS',
        'PRICE_MS',
        'STATUS_MS',
        'Price_Diff',
        'LINK_AC',
        'LINK_MS'
    ]].rename(columns={'UNIQUE_ID_AC': 'UNIQUE_ID'})

    final_report.to_excel(output_file, index=False)
    print(f"\nSUCCESS!", flush=True)
    print(f"Matching products found: {len(final_report)}", flush=True)
    print(f"Report saved as: {output_file}", flush=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--acoustic_file', required=True)
    parser.add_argument('--musikis_file', required=True)
    parser.add_argument('--output_file', required=True)
    args = parser.parse_args()
    compare_prices(args.acoustic_file, args.musikis_file, args.output_file)