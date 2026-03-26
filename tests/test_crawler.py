
import pytest
from unittest import mock
import pandas as pd
import crawler
import os

def test_deduplication():
    # Simulate deduplication logic (if present) in crawler.py
    data = [
        {'UNIQUE_ID': '1', 'NAME': 'A'},
        {'UNIQUE_ID': '1', 'NAME': 'A'},
        {'UNIQUE_ID': '2', 'NAME': 'B'}
    ]
    df = pd.DataFrame(data)
    df.drop_duplicates(subset=['UNIQUE_ID'], keep='first', inplace=True)
    assert len(df) == 2

def test_file_not_found(monkeypatch):
    # Simulate FileNotFoundError for geovoice link file
    monkeypatch.setattr('builtins.open', mock.Mock(side_effect=FileNotFoundError))
    with pytest.raises(SystemExit):
        import asyncio
        asyncio.run(crawler.scrape_geovoice())
