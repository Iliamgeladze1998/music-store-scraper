# 🎸 Music Store Market Analyzer (Acoustic vs Geovoice)

This project is an automated web scraping and data analysis tool designed to compare product prices and inventory status between two major musical instrument retailers in Georgia: **Acoustic.ge** and **Geovoice.ge**.

## 🚀 How the Process Works (Workflow)

The system is managed by a central **Master App** that executes a multi-stage pipeline. The process ensures data consistency by following these steps:

1.  **🔍 Link Collection:**
    * `get_links.py`: Scans **Acoustic.ge** to gather all product URLs.
    * `geovoice_get_links.py`: Scans **Geovoice.ge** to extract all individual product pages.

2.  **📦 Data Extraction (Scraping):**
    * `scraper.py`: Visits each Acoustic link to extract the product name, price, and stock status.
    * `crawler.py`: Performs the same extraction for all Geovoice links.

3.  **⚖️ Market Comparison:**
    * `compare_prices.py`: Merges both databases. It utilizes a **Fuzzy Matching** algorithm to accurately pair products with similar names or model numbers. It calculates price differences and identifies stock availability across both stores.

4.  **📊 Final Reporting:**
    * Generates a time-stamped Excel report (e.g., `FINAL_MARKET_ANALYSIS_0323_1200.xlsx`) for easy review.

## 🛠️ Execution

To run the entire market analysis cycle, you only need to execute the Master App:

```bash
python master_app.py
Note: The master_app.py is configured to automatically Commit and Push the latest results and code changes to GitHub after the analysis is complete.

🧰 Tech Stack
Python 3.x

Playwright (Web Automation & Scraping)

Pandas (Data Manipulation)

TheFuzz (String Matching & Comparison)

OpenPyXL (Excel Reporting)

Git/GitHub (Version Control & Automation)