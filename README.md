# 🎸 Music Store Market Analyzer (Acoustic vs Musikis Saxli)



A robust, fully automated Python pipeline for scraping, comparing, and reporting product prices and inventory between Georgia’s leading music retailers: **Acoustic.ge** and **Musikis Saxli**.



---



## 🚦 Workflow Overview



The pipeline is orchestrated by master_app.py and consists of the following stages:



1. **Link Collection**

   - get_links.py: Collects all category/product links from Acoustic.ge.

   - musikis-saxli-get-links.py: Collects all category links from Musikis Saxli.

   - musikis-saxli-get-all-product-links.py: Collects all product links from Musikis Saxli.



2. **Data Extraction**

   - scraper.py: Scrapes product data (name, price, status, ID, link) from Acoustic.ge using Playwright.

   - musikis-saxli-scraper.py: Scrapes product data from Musikis Saxli.



3. **Price Comparison**

   - compare_prices.py: Compares Acoustic and Musikis Saxli inventories using fuzzy matching, generating a detailed Excel report.



4. **Reporting & Delivery**

   - The final report is uploaded to Google Sheets and emailed to the configured recipient.

   - All steps are logged to automation.log for full transparency and auditability.



---



## 🛠️ Setup Instructions



1. **Clone the Repository**

   ```bash

   git clone https://github.com/Iliamgeladze1998/music-store-scraper.git

   cd MyProject2

   ```



2. **Install Python Dependencies**

   ```bash

   pip install -r requirements.txt

   playwright install

   ```



3. **Environment Configuration**

   - Create a .env file in the project root:

     ```

     MAIL_PASS=your_email_password

     SENDER_EMAIL=your_email@example.com

     RECIPIENT_EMAIL=recipient@example.com

     SPREADSHEET_ID=your_google_sheet_id

     TIMEZONE=Asia/Tbilisi

     ```

   - Place your `credentials.json` (Google Service Account) in the project root.



4. **Run the Pipeline**

   ```bash

   python master_app.py

   ```



   - All intermediate and final reports are timestamped and archived automatically.

   - Logs are written to `automation.log`.



5. **Testing**

   ```bash

   pytest tests/

   ```



---



## 🧑‍💻 Project Structure



- `master_app.py` — Orchestrates the full pipeline, error handling, reporting, and delivery.

- `get_links.py`, `musikis-saxli-get-links.py`, `musikis-saxli-get-all-product-links.py` — Link collection scripts.

- `scraper.py`, `musikis-saxli-scraper.py` — Data extraction (scraping) scripts.

- `compare_prices.py` — Price and inventory comparison logic.

- `requirements.txt` — All Python dependencies.

- `credentials.json`, `.env` — Sensitive configuration (never commit these to public repos).

- `tests/` — Unit and integration tests.



---



## 🧰 Tech Stack



- Python 3.x

- Playwright (async, for robust web scraping)

- Pandas, OpenPyXL (data processing and Excel reporting)

- gspread, oauth2client (Google Sheets API)

- TheFuzz (fuzzy string matching)

- Logging, dotenv, pytest



---



## 📝 Notes & Best Practices



- All secrets and credentials are loaded from `.env` and `credentials.json`.

- The pipeline is designed for local execution; no cloud automation is required.

- For troubleshooting, consult `automation.log` for detailed step-by-step logs.

- The system is robust to errors: failed steps trigger email alerts with error details.



---



Replace `<your-username>/<repo-name>` with your actual GitHub details.  

Let me know if you want this written directly to your README.md or need further customization!---



## 🧑‍💻 Project Structure



- `master_app.py` — Orchestrates the full pipeline, error handling, reporting, and delivery.

- `get_links.py`, `musikis-saxli-get-links.py`, `musikis-saxli-get-all-product-links.py` — Link collection scripts.

- `scraper.py`, `musikis-saxli-scraper.py` — Data extraction (scraping) scripts.

- `compare_prices.py` — Price and inventory comparison logic.

- `requirements.txt` — All Python dependencies.

- `credentials.json`, `.env` — Sensitive configuration