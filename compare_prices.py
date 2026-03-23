import pandas as pd
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def find_file(keyword):
    """ Automatically finds geovoice or acoustic files """
    files = [f for f in os.listdir('.') if keyword.lower() in f.lower() and (f.endswith('.csv') or f.endswith('.xlsx'))]
    if not files: return None
    latest = max(files, key=os.path.getctime)
    print(f"--- Loading: {latest} ---")
    if latest.endswith('.csv'):
        return pd.read_csv(latest)
    return pd.read_excel(latest)

def clean_name(text):
    """ Cleans product names for better ML matching """
    t = str(text).lower()
    t = re.sub(r'[ა-ჰ]', '', t) # Remove Georgian letters
    t = re.sub(r'[^a-z0-9 ]', ' ', t) # Keep only alphanumeric
    return " ".join(t.split())

def main():
    print("--- Starting ML Price Comparison (Feedback Mode) ---")
    
    df_gv = find_file("geovoice")
    df_ac = find_file("acoustic")
    
    report_file = 'FINAL_ML_MATCHES.xlsx'
    wrong_pairs = set()

    # STEP 1: Learn from previous mistakes if the file exists
    if os.path.exists(report_file):
        try:
            old_df = pd.read_excel(report_file)
            if 'Comment' in old_df.columns:
                # Find rows where user wrote 'WRONG'
                wrongs = old_df[old_df['Comment'].astype(str).str.upper() == 'WRONG']
                for _, row in wrongs.iterrows():
                    wrong_pairs.add((row['Name_GV'], row['Name_AC']))
                if len(wrong_pairs) > 0:
                    print(f"--- Successfully learned to avoid {len(wrong_pairs)} wrong matches ---")
        except Exception as e:
            print(f"Note: Could not read previous report for learning: {e}")

    if df_gv is None or df_ac is None:
        print("Error: Base inventory files not found!")
        return

    # STEP 2: Prepare names for ML
    gv_list = df_gv['Name'].apply(clean_name).tolist()
    ac_list = df_ac['Name'].apply(clean_name).tolist()

    # STEP 3: ML Vectorization (TF-IDF)
    # Using 1-4 n-grams to capture model numbers perfectly
    vectorizer = TfidfVectorizer(ngram_range=(1, 4), analyzer='char_wb')
    vectorizer.fit(gv_list + ac_list)
    
    gv_matrix = vectorizer.transform(gv_list)
    ac_matrix = vectorizer.transform(ac_list)

    # STEP 4: Calculate Cosine Similarity
    similarities = cosine_similarity(gv_matrix, ac_matrix)
    
    results = []
    threshold = 0.60 # Lower threshold to find MORE than 71 items

    for i, row in enumerate(similarities):
        best_match_idx = row.argmax()
        score = row[best_match_idx]
        
        gv_name = df_gv.iloc[i]['Name']
        ac_name = df_ac.iloc[best_match_idx]['Name']

        # Skip if this pair was previously marked as WRONG
        if (gv_name, ac_name) in wrong_pairs:
            continue

        if score >= threshold:
            # Basic Brand Check (First word) to prevent cross-brand errors
            gv_brand = str(gv_name).split()[0].upper()
            ac_brand = str(ac_name).split()[0].upper()
            
            if gv_brand == ac_brand:
                results.append({
                    'Brand': gv_brand,
                    'Name_GV': gv_name,
                    'Name_AC': ac_name,
                    'Similarity': round(score, 2),
                    'Price_GV': df_gv.iloc[i].get('Price (₾)', 0),
                    'Price_AC': df_ac.iloc[best_match_idx].get('Price (₾)', 0),
                    'Diff': df_gv.iloc[i].get('Price (₾)', 0) - df_ac.iloc[best_match_idx].get('Price (₾)', 0),
                    'Comment': '', # User can type WRONG here
                    'Link_GV': df_gv.iloc[i].get('Link', ''),
                    'Link_AC': df_ac.iloc[best_match_idx].get('Link', '')
                })

    if results:
        final_df = pd.DataFrame(results).drop_duplicates(subset=['Link_GV', 'Link_AC'])
        final_df = final_df.sort_values(by='Similarity', ascending=False)
        final_df.to_excel(report_file, index=False)
        print(f"\nCOMPLETED! Found {len(final_df)} items.")
        print(f"Open '{report_file}', mark errors as 'WRONG' in Comment column, and run again to improve.")
    else:
        print("No matches found. Try lowering threshold in code.")

if __name__ == "__main__":
    main()