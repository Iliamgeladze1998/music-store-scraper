import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeovoiceLinkCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Main category URLs provided by user
        self.main_categories = [
            "https://geovoice.ge/audio/",
            "https://geovoice.ge/dj-studia/", 
            "https://geovoice.ge/video-aparatura/",
            "https://geovoice.ge/sasceno-ganateba/",
            "https://geovoice.ge/komutacia/",
            "https://geovoice.ge/sadgamebi-sakidebi/",
            "https://geovoice.ge/bose-products/",
            "https://geovoice.ge/sale/"
        ]
        
    def get_all_category_pages(self):
        """Get all paginated pages for all categories."""
        logger.info("Starting Geovoice category pagination...")
        
        all_category_pages = []
        
        for category_url in self.main_categories:
            logger.info(f"Processing category: {category_url}")
            
            # Start with page 1 (the base URL)
            page = 1
            category_pages = []
            
            while True:
                if page == 1:
                    page_url = category_url  # First page is the base URL
                else:
                    page_url = f"{category_url}page-{page}/"
                
                logger.info(f"Testing page {page}: {page_url}")
                
                try:
                    response = self.session.get(page_url, timeout=10)
                    
                    # Check if page exists
                    if response.status_code == 404:
                        logger.info(f"Page {page} not found (404). Category finished.")
                        break
                    elif response.status_code != 200:
                        logger.error(f"Page {page} returned status {response.status_code}. Category finished.")
                        break
                    
                    # Check if page has actual content (not empty or error page)
                    if len(response.text) < 1000:  # Basic content check
                        logger.info(f"Page {page} appears empty. Category finished.")
                        break
                    
                    # Page exists and has content
                    category_pages.append(page_url)
                    logger.info(f"✅ Page {page} is valid")
                    
                    page += 1
                    
                    # Be respectful to the server
                    time.sleep(0.5)
                    
                except requests.RequestException as e:
                    logger.error(f"Error accessing page {page}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error on page {page}: {e}")
                    break
            
            logger.info(f"Category {category_url} has {len(category_pages)} pages")
            all_category_pages.extend(category_pages)
        
        logger.info(f"Total category pages collected: {len(all_category_pages)}")
        return all_category_pages
    
    def save_category_pages_to_file(self, pages, filename="geovoice_category_links.txt"):
        """Save all category page links to file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for page_url in pages:
                    f.write(page_url + '\n')
            logger.info(f"Saved {len(pages)} category page links to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving category page links: {e}")
            return False

def main():
    """Main execution for Geovoice category pagination."""
    logger.info("=== Geovoice Category Pagination Started ===")
    
    # Collect all category pages with pagination
    collector = GeovoiceLinkCollector()
    category_pages = collector.get_all_category_pages()
    
    if category_pages:
        if collector.save_category_pages_to_file(category_pages):
            logger.info("✅ All category page links saved successfully!")
            logger.info(f"Ready for product link collection from {len(category_pages)} pages")
        else:
            logger.error("❌ Failed to save category page links!")
    else:
        logger.error("❌ No category page links found!")

if __name__ == "__main__":
    main()
