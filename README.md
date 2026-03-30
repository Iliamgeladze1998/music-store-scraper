# 🎸 Multi-Competitor Price Intelligence System

A sophisticated, fully automated Python pipeline for real-time price comparison and inventory analysis across Georgia's leading music retailers. The system supports **Acoustic.ge** vs **Musikis Saxli** and **Acoustic.ge** vs **Geovoice.ge** comparisons with tab-specific Google Sheets integration.

---

## 🏗️ System Architecture

### **Multi-Competitor Workflow Design**

The system is built around independent, modular workflows that can operate individually or as a unified pipeline:

```
┌─────────────────┐    ┌─────────────────┐
│   Acoustic.ge   │    │  Musikis Saxli  │
│   (Base Store)  │    │  (Competitor)   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌─────────────────┐
          │  Price Compare  │
          │  Engine         │
          └─────────┬───────┘
                    │
          ┌─────────────────┐
          │  Google Sheets  │
          │  'Musikis-saxli'│
          └─────────────────┘

┌─────────────────┐    ┌─────────────────┐
│   Acoustic.ge   │    │    Geovoice     │
│   (Base Store)  │    │  (Competitor)   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌─────────────────┐
          │  Price Compare  │
          │  Engine         │
          └─────────┬───────┘
                    │
          ┌─────────────────┐
          │  Google Sheets  │
          │    'Geovoice'   │
          └─────────────────┘
```

### **Core Components**

#### **1. Master Orchestrators**
- **`master_app.py`** - Musikis Saxli workflow manager
- **`master_geovoice.py`** - Geovoice workflow manager  
- **`run_all_comparisons.py`** - Unified runner for both workflows

#### **2. Data Collection Pipeline**
- **Link Discovery**: Automated category and product link extraction
- **Pagination Handling**: Intelligent page traversal with 404 detection
- **Product Scraping**: Structured data extraction (name, price, SKU, status, links)

#### **3. Price Comparison Engine**
- **SKU-Based Matching**: Direct product identifier comparison
- **Signed Price Differences**: `Price_Diff = Price_Competitor - Price_Acoustic`
- **Standardized Output**: Consistent column structure across all competitors

#### **4. Google Sheets Integration**
- **Tab-Specific Uploads**: Isolated worksheets for each competitor
- **Clean Slate Logic**: Complete formatting reset before each upload
- **Timestamp Tracking**: Automatic update timestamps in K1 cells

---

## 🔄 Data Workflow

### **Stage 1: Link Collection**
```
Acoustic.ge → get_links.py → acoustic_category_links.txt
Musikis → musikis-saxli-get-links.py → pagination → musikis_category_links.txt
Geovoice → geovoice-get-links.py → pagination → geovoice_category_links.txt
```

### **Stage 2: Product Link Extraction**
```
Category Pages → get-all-product-links.py → all_product_links.txt
(Handles 1,500+ product URLs per competitor)
```

### **Stage 3: Data Scraping**
```
Product URLs → scraper.py → acoustic_inventory_[timestamp].xlsx
Product URLs → musikis-saxli-scraper.py → musikis_inventory.csv
Product URLs → geovoice_scraper.py → geovoice_inventory.csv
```

### **Stage 4: Price Comparison**
```
Acoustic Data + Competitor Data → compare_prices.py → 
COMPETITOR_REPORT_[timestamp].xlsx
```

### **Stage 5: Google Sheets Upload**
```
Report File → Tab-Specific Upload → Clean Formatting → Timestamp Update
```

---

## 📊 Google Sheets Structure

### **Tab 1: 'Musikis-saxli'**
| UNIQUE_ID | NAME_AC | PRICE_AC | STATUS_AC | NAME_MS | PRICE_MS | STATUS_MS | Price_Diff | LINK_AC | LINK_MS |
|-----------|---------|-----------|-----------|---------|----------|-----------|------------|---------|---------|

### **Tab 2: 'Geovoice'**  
| UNIQUE_ID | NAME_AC | PRICE_AC | STATUS_AC | NAME_GV | PRICE_GV | STATUS_GV | Price_Diff | LINK_AC | LINK_GV |
|-----------|---------|-----------|-----------|---------|----------|-----------|------------|---------|---------|

**Key Features:**
- **Signed Price Differences**: Positive = Competitor more expensive
- **Complete Link Tracking**: Both store URLs for each matched product
- **Status Monitoring**: Real-time stock availability comparison
- **Clean Formatting**: Automatic reset of colors, filters, and styles

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.8+
- Google Service Account credentials
- Google Sheets API access

### **1. Clone Repository**
```bash
git clone https://github.com/Iliamgeladze1998/music-store-scraper.git
cd MyProject2
```

### **2. Install Dependencies**
```bash
pip install requests pandas openpyxl gspread oauth2client
pip install beautifulsoup4 playwright thefuzz
pip install python-dotenv smtplib
playwright install
```

### **3. Configuration**
Create `credentials.json` (Google Service Account):
```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "your-service-account@gserviceaccount.com"
}
```

### **4. Google Sheets Setup**
- Create spreadsheet with ID in CONFIG
- Add two tabs: 'Musikis-saxli' and 'Geovoice'
- Share with service account email

---

## 🎯 Usage Scenarios

### **Full Production Run**
```bash
# Run both competitors sequentially
python run_all_comparisons.py
```

### **Individual Workflows**
```bash
# Music Store comparison only
python master_app.py

# Geovoice comparison only  
python master_geovoice.py
```

### **Quick Testing**
```bash
# Test uploads with existing data
python test_unified_runner.py

# Test individual tab uploads
python test_sheets_upload.py    # Geovoice tab
python quick_upload.py         # Musikis-saxli tab
```

---

## 🔧 Technical Implementation

### **Error Handling & Resilience**
- **Timeout Protection**: 2-hour limits for long-running operations
- **Graceful Failures**: Continue pipeline despite individual step failures
- **Comprehensive Logging**: Detailed execution logs for troubleshooting
- **Email Alerts**: Automatic failure notifications (Music Store only)

### **Data Integrity**
- **Session-Based Naming**: Timestamped files prevent data conflicts
- **Clean Slate Uploads**: Complete formatting reset ensures consistency
- **SKU Validation**: Direct product ID matching prevents false positives
- **Price Cleaning**: Automatic currency symbol and comma removal

### **Performance Optimization**
- **Concurrent Processing**: Parallel link collection and scraping
- **Rate Limiting**: Respectful request delays (0.5-1 second intervals)
- **Memory Management**: Efficient DataFrame operations for large datasets
- **Incremental Updates**: Only process new/changed products when possible

---

## 📋 Requirements

### **Core Dependencies**
```
requests>=2.28.0          # HTTP requests
pandas>=1.5.0            # Data manipulation
openpyxl>=3.0.0          # Excel file handling
gspread>=5.7.0           # Google Sheets API
oauth2client>=4.1.0      # Google OAuth
beautifulsoup4>=4.11.0   # HTML parsing
playwright>=1.30.0       # Browser automation
thefuzz>=0.20.0          # Fuzzy string matching
python-dotenv>=0.19.0    # Environment variables
```

### **System Requirements**
- **Memory**: 4GB+ RAM (for large dataset processing)
- **Storage**: 1GB+ free space (for logs and reports)
- **Network**: Stable internet connection (for web scraping)
- **OS**: Windows/Linux/macOS with Python 3.8+

---

## 🧪 Testing & Validation

### **Unit Tests**
```bash
pytest tests/test_scraper.py
pytest tests/test_logic.py
pytest tests/test_master_app.py
```

### **Integration Tests**
```bash
python test_geovoice_compare.py      # Price comparison logic
python test_sheets_upload.py       # Google Sheets upload
python test_unified_runner.py       # End-to-end workflow
```

### **Data Validation**
- **SKU Matching**: Verify correct product identification
- **Price Accuracy**: Confirm mathematical calculations
- **Link Validity**: Test URL accessibility
- **Format Consistency**: Ensure standardized output structure

---

## 📈 Monitoring & Maintenance

### **Log Files**
- `automation.log` - Main pipeline execution
- `geovoice_automation.log` - Geovoice-specific operations
- `run_all_comparisons.log` - Unified runner logs

### **Performance Metrics**
- **Scraping Speed**: Products processed per minute
- **Match Rate**: Percentage of products with price comparisons
- **Upload Success**: Google Sheets integration reliability
- **Error Frequency**: Failed operations and recovery rates

### **Maintenance Tasks**
- **Credentials Rotation**: Update Google Service Account keys quarterly
- **Selector Updates**: Adjust CSS selectors when websites change
- **Capacity Planning**: Monitor storage usage for growing datasets
- **Performance Tuning**: Optimize timeouts and retry logic

---

## 🔒 Security Considerations

### **Data Protection**
- **Local Storage**: Sensitive credentials stored locally, not in code
- **Environment Variables**: Email passwords and API keys externalized
- **Access Control**: Google Sheets shared only with service accounts
- **Audit Trail**: Comprehensive logging for compliance monitoring

### **Web Scraping Ethics**
- **Rate Limiting**: Respectful request intervals prevent server overload
- **User-Agent Headers**: Proper browser identification
- **Error Handling**: Graceful failure without server disruption
- **Data Usage**: Limited to price comparison purposes only

---

## 🚨 Troubleshooting

### **Common Issues**
1. **Google Sheets Authentication**
   - Verify `credentials.json` format and permissions
   - Check spreadsheet sharing settings
   - Confirm API access in Google Cloud Console

2. **Web Scraping Failures**
   - Update CSS selectors for website changes
   - Check internet connectivity and firewall settings
   - Verify Playwright browser installation

3. **Memory Issues**
   - Close unnecessary applications
   - Process data in smaller batches
   - Increase system RAM if needed

4. **Timeout Errors**
   - Increase timeout values in configuration
   - Check network stability
   - Verify server response times

### **Debug Mode**
```bash
# Enable verbose logging
export PYTHONPATH=.
python -u master_app.py 2>&1 | tee debug.log
```

---

## 📞 Support & Contributing

### **Getting Help**
- Review `automation.log` for detailed error messages
- Check Google Sheets permissions and sharing settings
- Verify all configuration files are properly formatted

### **Contributing Guidelines**
1. Fork the repository
2. Create feature branch for new functionality
3. Add comprehensive tests for new features
4. Update documentation for API changes
5. Submit pull request with detailed description

---

## 📄 License & Attribution

This project is provided for educational and research purposes. Users are responsible for ensuring compliance with website terms of service and applicable data protection regulations.

**Disclaimer**: This system is designed for legitimate price comparison and market research. Users must respect robots.txt files, rate limits, and all applicable laws and regulations.

---

*Last Updated: March 2026*  
*System Version: 2.0 - Multi-Competitor Architecture*