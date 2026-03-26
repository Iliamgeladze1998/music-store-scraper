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

## 🛠️ Local-Only Execution

This project is now designed for 100% local execution. No GitHub Actions or cloud automation is required.

### 1. Setup

- Clone/download the repository to your local machine.
- Install Python 3.x and dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Create a `.env` file in the project root with your sensitive variables:
  ```env
  MAIL_PASS=your_email_password_here
  SENDER_EMAIL=your_email@example.com
  RECIPIENT_EMAIL=recipient@example.com
  SPREADSHEET_ID=your_google_sheet_id
  # Add other variables as needed
  ```
- Place your `credentials.json` (Google API credentials) in the project root.

### 2. Run the Full Pipeline

```bash
python master_app.py
```

### 3. Run Tests

```bash
pytest tests/
```

## 🧰 Tech Stack

- Python 3.x
- Playwright (Web Automation & Scraping)
- Pandas (Data Manipulation)
- TheFuzz (String Matching & Comparison)
- OpenPyXL (Excel Reporting)
- gspread, oauth2client (Google Sheets API)
- pytest (Testing)

## Notes

- All sensitive data is now loaded from `.env` and `credentials.json` in the project root.
- No GitHub Actions or cloud automation is used. All scripts are run locally.
- For any issues, check `automation.log` for detailed logs.