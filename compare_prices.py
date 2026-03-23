import pandas as pd
import glob
import os
import re
from thefuzz import fuzz
from sentence_transformers import SentenceTransformer, util

# Load a lightweight AI model for Semantic Meaning
# This model understands that "Essential" vs "MK3" are different tiers
print("🤖 Loading AI Semantic Model... Please wait.")
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return max(files, key=os.path.getctime) if files else None

def extract_strict_tokens(name):
    """Extracts model numbers and numeric codes (e.g., 825, ME2, TD-3)"""
    return set(re.findall(r'\b\w*\d\w*\b', name.upper()))

def is_valid_match(name1, name2, price1, price2, semantic_score):
    n1, n2 = name1.upper(), name2.upper()
    
    # 1. PRICE FILTER (35% margin)
    try:
        p1, p2 = float(price1), float(price2)
        if max(p1, p2) > 0 and abs(p1 - p2) / max(p1, p2) > 0.35:
            return False
    except:
        return False

    # 2. SEMANTIC THRESHOLD (The AI Check)
    # If AI thinks they are contextually different, reject them
    if semantic_score < 0.70:
        return False

    # 3. STRICT MODEL CHECK
    tokens1 = extract_strict_tokens(n1)
    tokens2 = extract_strict_tokens(n2)
    if tokens1 and tokens2 and not (tokens1 & tokens2):
        return False

    # 4. KEYWORD BLACKLIST (Crucial for tiers)
    blacklist = ['ESSENTIAL', 'SET', 'KIT', 'BUNDLE', 'MO', 'PRO', 'LAVALIER', 'VOCAL']
    for word in blacklist:
        if (word in n1 and word not in n2) or (word in n2 and word not in n1):
            return False

    return True

def run_ai_comparison():
    print("🚀 Starting AI-Powered Market Analysis...")

    gv_file = get_latest_file("geovoice_full_inventory.csv")
    ac_file = get_latest_file("acoustic_inventory_*.xlsx")

    if not gv_file or not ac_file:
        print("❌ Error: Files not found!")
        return

    df_gv = pd.read_csv(gv_file)
    df_ac = pd.read_excel(ac_file)
    ac_list = df_ac.to_dict('records')

    # Pre-calculate Embeddings for Acoustic names to save time
    print("⏳ Analyzing Acoustic.ge inventory semantics...")
    ac_names = [str(item['Name']) for item in ac_list]
    ac_embeddings = model.encode(ac_names, convert_to_tensor=True)

    matched_data = []

    print(f"🔬 Cross-referencing {len(df_gv)} items with AI Semantic Logic...")

    for i, gv_row in df_gv.iterrows():
        gv_name = str(gv_row['Name']).strip()
        gv_price = gv_row['Price (₾)']
        
        # Calculate AI similarity for the current GV item against ALL AC items at once
        gv_embedding = model.encode(gv_name, convert_to_tensor=True)
        cos_scores = util.cos_sim(gv_embedding, ac_embeddings)[0]

        for idx, ac_item in enumerate(ac_list):
            semantic_score = cos_scores[idx].item()
            ac_name = str(ac_item['Name']).strip()
            
            # If AI similarity is high, run our strict logical filters
            if semantic_score >= 0.75: 
                if is_valid_match(gv_name, ac_name, gv_price, ac_item['Price (₾)'], semantic_score):
                    matched_data.append({
                        'AI Confidence %': round(semantic_score * 100, 1),
                        'Name (Geovoice)': gv_name,
                        'Name (Acoustic)': ac_name,
                        'Price GV': gv_price,
                        'Price AC': ac_item['Price (₾)'],
                        'Diff': round(float(gv_price) - float(ac_item['Price (₾)']), 2),
                        'Link GV': gv_row['Link'],
                        'Link AC': ac_item['Link']
                    })

    if matched_data:
        final_df = pd.DataFrame(matched_data).drop_duplicates(subset=['Name (Geovoice)', 'Name (Acoustic)'])
        final_df = final_df.sort_values(by='AI Confidence %', ascending=False)
        output = f"AI_MARKET_REPORT_{pd.Timestamp.now().strftime('%H%M')}.xlsx"
        final_df.to_excel(output, index=False)
        print(f"✅ Success! Found {len(final_df)} AI-verified matches.")
    else:
        print("⚠️ No reliable matches found.")

if __name__ == "__main__":
    run_ai_comparison()