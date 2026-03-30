import pandas as pd

# Test the corrected math logic
df = pd.read_excel('RE_RUN_REPORT_NEW.xlsx')

print('=== Price Difference Analysis (Corrected Math) ===')
print(f'Total products: {len(df)}')
print()
print('Sample Price_Diff values (PRICE_MS - PRICE_AC):')
print(df[['PRICE_AC', 'PRICE_MS', 'Price_Diff']].head(10))
print()
print('Price_Diff Statistics:')
print(f'Min (most negative): {df["Price_Diff"].min():.2f}')
print(f'Max (most positive): {df["Price_Diff"].max():.2f}')
print(f'Average: {df["Price_Diff"].mean():.2f}')
print()
print('Interpretation:')
print('Negative = Musikis Saxli CHEAPER than Acoustic (good deal!)')
print('Positive = Musikis Saxli MORE EXPENSIVE than Acoustic')
print('Zero = Same price')
print()
print('Example Analysis:')
for idx, row in df.head(3).iterrows():
    diff = row['Price_Diff']
    if diff < 0:
        print(f"  {row['NAME_MS'][:30]}... Musikis {row['PRICE_MS']} vs Acoustic {row['PRICE_AC']} = {diff:.2f} (MUSIKIS CHEAPER)")
    elif diff > 0:
        print(f"  {row['NAME_MS'][:30]}... Musikis {row['PRICE_MS']} vs Acoustic {row['PRICE_AC']} = {diff:.2f} (MUSIKIS MORE EXPENSIVE)")
    else:
        print(f"  {row['NAME_MS'][:30]}... Musikis {row['PRICE_MS']} vs Acoustic {row['PRICE_AC']} = {diff:.2f} (SAME PRICE)")
