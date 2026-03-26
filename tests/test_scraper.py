
import pandas as pd
import pytest
import os

def test_deduplication_logic():
    # Test deduplication logic as used in scraper.py
    data = [
        {'UNIQUE_ID': '1', 'NAME': 'A'},
        {'UNIQUE_ID': '1', 'NAME': 'A'},
        {'UNIQUE_ID': '2', 'NAME': 'B'}
    ]
    df = pd.DataFrame(data)
    df.drop_duplicates(subset=['UNIQUE_ID'], keep='first', inplace=True)
    assert len(df) == 2

def test_missing_subcategory_links(monkeypatch, capsys):
    # Simulate FileNotFoundError for subcategory_links.txt
    monkeypatch.setattr('builtins.open', lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError))
    from scraper import scrape_acoustic
    import asyncio
    asyncio.run(scrape_acoustic())
    captured = capsys.readouterr()
    assert "subcategory_links.txt not found" in captured.out
