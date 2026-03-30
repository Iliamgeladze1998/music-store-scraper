import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeovoiceScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.products = []
        
    def clean_price(self, price_text):
        """Extract numeric price from text and convert to integer."""
        if not price_text:
            return None
        
        # Remove currency symbols, commas, and any non-numeric characters except dots
        price_str = str(price_text).replace('₾', '').replace('GEL', '').replace('$', '').replace('€', '').replace(',', '').replace(' ', '').strip()
        
        try:
            # Convert to float first, then to int to handle decimal prices
            price_float = float(price_str)
            return int(price_float)
        except ValueError:
            return None
    
    def clean_sku(self, sku_text):
        """Clean SKU/UNIQUE_ID."""
        if not sku_text:
            return ""
        return str(sku_text).strip()
    
    def scrape_product(self, url):
        """Scrape individual product details using specific selectors."""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to access {url}: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract UNIQUE_ID using selector: span[id^="product_code_"]
            sku_elem = soup.find('span', id=lambda x: x and x.startswith('product_code_'))
            sku = self.clean_sku(sku_elem.get_text() if sku_elem else "")
            
            # Extract Product Name using selector: h1.ut2-pb__title bdi
            name_elem = soup.select_one('h1.ut2-pb__title bdi')
            name = name_elem.get_text().strip() if name_elem else "Unknown Product"
            
            # Extract Price using selector: span[id^="sec_discounted_price_"] .ty-price-num
            price_elem = soup.select_one('span[id^="sec_discounted_price_"] .ty-price-num')
            if not price_elem:
                # Fallback to any span with class ty-price-num
                price_elem = soup.find('span', class_='ty-price-num')
            
            price = self.clean_price(price_elem.get_text() if price_elem else None)
            
            # Extract Status using selector: span[id^="in_stock_info_"] inside stock-wrap
            status_elem = soup.select_one('.stock-wrap span[id^="in_stock_info_"]')
            status_text = status_elem.get_text().strip().lower() if status_elem else ""
            
            if "მარაგშია" in status_text:
                status = "In Stock"
            else:
                status = "Out of Stock"
            
            return {
                'UNIQUE_ID': sku,
                'Product_Name': name,
                'Price': price,
                'Status': status,
                'Link': url
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def scrape_all_products(self, links_file="geovoice_product_links.txt", max_products=None):
        """Main scraping method with optional limit for testing."""
        logger.info("Starting Geovoice product scraping...")
        
        # Read product links
        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                product_links = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error reading product links: {e}")
            return []
        
        # Limit products for testing if specified
        if max_products and len(product_links) > max_products:
            product_links = product_links[:max_products]
            logger.info(f"Testing with first {max_products} products (out of {len([line.strip() for line in open(links_file, 'r', encoding='utf-8').readlines() if line.strip()])} total)")
        else:
            logger.info(f"Processing all {len(product_links)} products")
        
        logger.info(f"Found {len(product_links)} product links to scrape")
        
        # Scrape each product
        for i, url in enumerate(product_links, 1):
            logger.info(f"[{i}/{len(product_links)}] Scraping: {url}")
            
            product = self.scrape_product(url)
            if product:
                self.products.append(product)
            
            # Progress update every 10 products
            if i % 10 == 0:
                logger.info(f"Scraped {i}/{len(product_links)} products...")
            
            # Add delay to be respectful
            time.sleep(0.5)
        
        logger.info(f"Successfully scraped {len(self.products)} products")
        return self.products
    
    def save_to_csv(self, filename="geovoice_inventory.csv"):
        """Save products to CSV with required columns."""
        if not self.products:
            logger.error("No products to save!")
            return False
            
        df = pd.DataFrame(self.products)
        
        # Ensure required columns in correct order
        df = df[['UNIQUE_ID', 'Product_Name', 'Price', 'Status', 'Link']]
        
        # Clean data
        df = df.drop_duplicates(subset=['UNIQUE_ID'])
        df = df.dropna(subset=['UNIQUE_ID'])
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} products to {filename}")
        return True

def main():
    """Main execution function."""
    logger.info("=== Geovoice Product Scraping Started ===")
    
    scraper = GeovoiceScraper()
    
    # Scrape all products
    products = scraper.scrape_all_products()
    
    # Save to CSV
    if scraper.save_to_csv():
        logger.info("🎉 Geovoice scraping completed successfully!")
        logger.info(f"Total products scraped: {len(scraper.products)}")
        logger.info("✅ geovoice_inventory.csv is ready for comparison!")
    else:
        logger.error("💥 Geovoice scraping failed!")

if __name__ == "__main__":
    main()
