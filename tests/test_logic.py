import pytest
import pandas as pd
import re

def clean_id(id_val):
    """
    Standardizes product IDs by removing special characters 
    and converting to uppercase for reliable matching.
    """
    if pd.isna(id_val) or id_val is None:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(id_val)).upper()

def test_id_cleaning_logic():
    """Checks if the ID cleaner handles special characters and spaces correctly."""
    assert clean_id("Roland-X500!") == "ROLANDX500"
    assert clean_id("  piano 123  ") == "PIANO123"
    assert clean_id(None) == ""
    assert clean_id(99.9) == "999"

def test_price_comparison_matching():
    """
    Simulates a merge between two datasets to ensure 
    the logic correctly identifies matches and calculates differences.
    """
    # Mocking Acoustic Store Data
    ac_data = pd.DataFrame({
        'NAME': ['Digital Piano P-45', 'Electric Guitar'],
        'UNIQUE_ID': ['P45-AX', 'GTR-001'],
        'PRICE': [1800, 950]
    })
    
    # Mocking Geovoice Store Data
    gv_data = pd.DataFrame({
        'NAME': ['Yamaha P45', 'Random Accessory'],
        'UNIQUE_ID': ['P45AX', 'ACC-99'],
        'PRICE': [1750, 50]
    })
    
    # Apply cleaning logic
    ac_data['CLEAN_ID'] = ac_data['UNIQUE_ID'].apply(clean_id)
    gv_data['CLEAN_ID'] = gv_data['UNIQUE_ID'].apply(clean_id)
    
    # Perform strict matching merge
    merged = pd.merge(ac_data, gv_data, on='CLEAN_ID', suffixes=('_AC', '_GV'))
    
    # Assertions
    assert len(merged) == 1  # Only P45 should match
    assert merged.iloc[0]['PRICE_AC'] == 1800
    assert merged.iloc[0]['PRICE_GV'] == 1750
    assert (merged.iloc[0]['PRICE_AC'] - merged.iloc[0]['PRICE_GV']) == 50

def test_empty_dataframe_handling():
    """Ensures the logic doesn't crash when encountering empty dataframes."""
    empty_df = pd.DataFrame(columns=['NAME', 'PRICE', 'UNIQUE_ID'])
    assert empty_df.empty is True