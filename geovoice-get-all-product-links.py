import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeovoiceProductLinkCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def collect_from_category_links(self, category_file="geovoice_category_links.txt"):
        """Collect all product links from category pages file using specific selectors."""
        logger.info(f"Reading category page links from {category_file}")
        
        try:
            with open(category_file, 'r', encoding='utf-8') as f:
                category_page_links = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error reading category page links: {e}")
            return False
        
        if not category_page_links:
            logger.error("No category page links found!")
            return False
        
        all_product_links = []
        
        for i, category_page_url in enumerate(category_page_links, 1):
            logger.info(f"Processing category page {i}/{len(category_page_links)}: {category_page_url}")
            
            try:
                response = self.session.get(category_page_url, timeout=10)
                if response.status_code != 200:
                    logger.error(f"Failed to access {category_page_url}: {response.status_code}")
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product containers using specific selector: div.ty-column4
                product_containers = soup.find_all('div', class_='ty-column4')
                
                page_product_links = []
                
                for container in product_containers:
                    # Find product links using specific selector: a.product-title
                    product_links = container.find_all('a', class_='product-title')
                    
                    for link_elem in product_links:
                        href = link_elem.get('href', '')
                        if href:
                            # Convert to absolute URL if needed
                            if href.startswith('http'):
                                full_url = href
                            elif href.startswith('/'):
                                full_url = "https://geovoice.ge" + href
                            else:
                                full_url = f"https://geovoice.ge/{href}"
                            
                            if full_url not in all_product_links:
                                page_product_links.append(full_url)
                
                logger.info(f"Extracted {len(page_product_links)} links from {category_page_url}")
                
                # Add to master list
                all_product_links.extend(page_product_links)
                
                # Be respectful to the server
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing category page {category_page_url}: {e}")
                continue
        
        # Remove duplicates
        unique_links = list(set(all_product_links))
        logger.info(f"Total unique product links collected: {len(unique_links)}")
        
        # Save to file
        try:
            with open("geovoice_product_links.txt", 'w', encoding='utf-8') as f:
                for link in unique_links:
                    f.write(link + '\n')
            logger.info("✅ Saved all product links to geovoice_product_links.txt")
            return True
        except Exception as e:
            logger.error(f"Error saving product links: {e}")
            return False

def main():
    """Main execution for Geovoice product link collection."""
    logger.info("=== Geovoice Product Link Collection Started ===")
    
    # Collect all product links from category pages
    collector = GeovoiceProductLinkCollector()
    if collector.collect_from_category_links():
        logger.info("🎉 All Geovoice product links collected successfully!")
        logger.info(f"Total links ready for scraping: {len([line.strip() for line in open('geovoice_product_links.txt', 'r', encoding='utf-8').readlines() if line.strip()])}")
        logger.info("✅ Ready for next step: Individual product scraping")
    else:
        logger.error("💥 Failed to collect product links!")

if __name__ == "__main__":
    main()
