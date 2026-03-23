import pandas as pd
import glob
import os
import re
from thefuzz import fuzz

def get_latest_file(pattern):
    """Finds the most recently created file matching the pattern"""
    files = glob.glob(pattern)
    return max(files, key=os.path.getctime) if files else None

def extract_model(name):
    """Extracts potential model numbers (combinations of letters and numbers)"""
    # Looks for words containing digits (e.g., SM7B, F310, C40)
    parts = re.findall(r'\b[A-Z0-9-]{2,}\b', name.upper())
    return set(parts)

def run_strict_comparison():
    print("🎯 Starting Strict Comparison (Model-Check Logic)...")

    gv_file = get_latest_file("geovoice_full_inventory.csv")
    ac_file = get_latest_file("acoustic_inventory_*.xlsx")

    if not gv_file or not ac_file:
        print("❌ Files not found!")
        return

    # Reading the data
    df_gv = pd.read_csv(gv_file)
    df_ac = pd.read_excel(ac_file)

    matched_data = []
    
    # Prepare Acoustic data (Indexing by first character for optimization)
    ac_list = []
    for _, row in df_ac.iterrows():
        name = str(row['Name']).strip()
        ac_list.append({
            'name': name,
            'first_char': name[0].upper() if name else "",
            'model_parts': extract_model(name),
            'data': row
        })

    print(f"⏳ Checking {len(df_gv)} items...")

    for _, gv_row in df_gv.iterrows():
        gv_name = str(gv_row['Name']).strip()
        gv_models = extract_model(gv_name)
        gv_first_char = gv_name[0].upper() if gv_name else ""

        for ac_item in ac_list:
            # 1. Optimization: First character must match
            if gv_first_char != ac_item['first_char']:
                continue
            
            # 2. Critical Check: If model numbers (e.g., SM7B) don't match, skip
            if gv_models and ac_item['model_parts']:
                if not (gv_models & ac_item['model_parts']): # Intersection check
                    continue

            # 3. Fuzzy Comparison (Only for items that passed the model check)
            score = fuzz.token_set_ratio(gv_name, ac_item['name'])
            
            # 🎯 Matching threshold set to 90
            if score >= 90:
                matched_data.append({
                    'Confidence %': score,
                    'Name (Geovoice)': gv_name,
                    'Name (Acoustic)': ac_item['name'],
                    'Price GV': gv_row['Price (₾)'],
                    'Price AC': ac_item['data']['Price (₾)'],
                    'Diff': float(gv_row['Price (₾)']) - float(ac_item['data']['Price (₾)']),
                    'Link GV': gv_row['Link'],
                    'Link AC': ac_item['data']['Link']
                })

    # Saving Results
    if matched_data:
        final_df = pd.DataFrame(matched_data).drop_duplicates(subset=['Name (Geovoice)', 'Name (Acoustic)'])
        final_df = final_df.sort_values(by='Confidence %', ascending=False)
        output = f"STRICT_REPORT_{pd.Timestamp.now().strftime('%H%M')}.xlsx"
        final_df.to_excel(output, index=False)
        print(f"✅ Success! Found {len(final_df)} exact matches. File saved as: {output}")
    else:
        print("⚠️ No common items were found.")

if __name__ == "__main__":
    run_strict_comparison()