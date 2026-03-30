import pandas as pd

# Create sample Geovoice data for testing
sample_data = [
    {
        'UNIQUE_ID': 'GEO001',
        'NAME': 'Geovoice Acoustic Guitar Model A',
        'PRICE': 850.0,
        'STATUS': 'In Stock',
        'LINK': 'https://geovoice.ge/product/guitar-a'
    },
    {
        'UNIQUE_ID': 'GEO002', 
        'NAME': 'Geovoice Electric Guitar Model B',
        'PRICE': 1200.0,
        'STATUS': 'In Stock',
        'LINK': 'https://geovoice.ge/product/guitar-b'
    },
    {
        'UNIQUE_ID': 'GEO003',
        'NAME': 'Geovoice Bass Guitar Model C', 
        'PRICE': 650.0,
        'STATUS': 'Out of Stock',
        'LINK': 'https://geovoice.ge/product/bass-c'
    },
    {
        'UNIQUE_ID': 'GEO004',
        'NAME': 'Geovoice Piano Model D',
        'PRICE': 2500.0,
        'STATUS': 'In Stock', 
        'LINK': 'https://geovoice.ge/product/piano-d'
    },
    {
        'UNIQUE_ID': 'GEO005',
        'NAME': 'Geovoice Microphone Model E',
        'PRICE': 180.0,
        'STATUS': 'In Stock',
        'LINK': 'https://geovoice.ge/product/mic-e'
    }
]

# Save to CSV
df = pd.DataFrame(sample_data)
df.to_csv('geovoice_inventory.csv', index=False, encoding='utf-8')
print(f"Created sample geovoice_inventory.csv with {len(df)} products")
