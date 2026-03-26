
import pandas as pd
import re
from datetime import datetime
import asyncio
import logging
from base_scraper import BaseScraper
from config import ACOUSTIC_SELECTORS, SCRAPER_CONFIG

class AcousticScraper(BaseScraper):
    def __init__(self, logger=None):
        super().__init__(ACOUSTIC_SELECTORS, logger=logger)

    async def process_page(self, page, url):
        products_data = []
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            if not response or response.status != 200:
                self.logger.warning(f"HTTP {getattr(response, 'status', 'N/A')} for {url}")
                return products_data
            try:
                await page.wait_for_selector(self.selectors['product_container'], timeout=5000)
            except:
                pass
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
            except:
                pass
            products = await page.query_selector_all(self.selectors['product_container'])
            valid_id_count = 0
            missing_id_count = 0
            for product in products:
                try:
                    name_el = await product.query_selector(self.selectors['name'])
                    if not name_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    link = await name_el.get_attribute("href")
                    unique_id = "N/A"
                    original_id = None
                    for selector in self.selectors['sku']:
                        try:
                            sku_el = await product.query_selector(selector)
                            if sku_el:
                                original_id = await sku_el.inner_text()
                                unique_id = str(original_id).strip().upper()
                                break
                        except:
                            continue
                    self.logger.info(f"[DEBUG] Product: '{name}' | Extracted ID: '{original_id}' | URL: {url}")
                    if not original_id or unique_id == "N/A" or unique_id == "":
                        missing_id_count += 1
                        self.logger.warning(f"[WARNING] No ID found for product '{name}' at {url}.")
                    else:
                        valid_id_count += 1
                    price_val = "0"
                    try:
                        price_container = await product.query_selector(self.selectors['price'])
                        if price_container:
                            raw_text = (await price_container.inner_text()).strip()
                            digits = "".join(re.findall(r'\d+', raw_text))
                            if digits.endswith("00") and len(digits) > 2:
                                price_val = digits[:-2]
                            else:
                                price_val = digits
                    except:
                        pass
                    status = "In Stock"
                    try:
                        product_text = await product.inner_text()
                        if any(s in product_text for s in self.selectors['status_text']):
                            status = "Out of Stock"
                    except:
                        pass
                    products_data.append({
                        'UNIQUE_ID': unique_id,
                        'NAME': name,
                        'PRICE': price_val,
                        'STATUS': status,
                        'LINK': link,
                        'DATE': datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                except Exception as e:
                    self.logger.warning(f"Product parse error: {e}")
            self.logger.info(f"[SUMMARY] {url} -> Found {len(products_data)} products. {valid_id_count} have IDs, {missing_id_count} are missing IDs.")
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout loading {url}")
        except Exception as e:
            self.logger.warning(f"Error: {str(e)[:40]} at {url}")
        return products_data

async def scrape_acoustic():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"acoustic_inventory_{timestamp}.xlsx"
    start_time = datetime.now()
    try:
        with open("subcategory_links.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        if not urls:
            print("Error: subcategory_links.txt is empty!")
            return
        print(f"Starting scrape: {len(urls)} categories found\n", flush=True)
    except FileNotFoundError:
        print("Error: subcategory_links.txt not found!")
        return
    logger = logging.getLogger("acoustic")
    scraper = AcousticScraper(logger=logger)
    all_data = []
    # Producer-consumer: gather links, then process in parallel
    results = await scraper.run(urls, scraper.process_page)
    for batch in results:
        if batch:
            all_data.extend(batch)
    if all_data:
        df = pd.DataFrame(all_data)
        df.drop_duplicates(subset=['UNIQUE_ID'], keep='first', inplace=True)
        df.to_excel(file_name, index=False)
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n{'='*50}")
        print(f"COMPLETE!")
        print(f"   Total items: {len(df)}")
        print(f"   Time: {elapsed:.1f}s ({elapsed/len(urls):.1f}s per category)")
        print(f"   Saved: {file_name}")
        print(f"{'='*50}\n", flush=True)
    else:
        print("\nNo data collected.", flush=True)

if __name__ == "__main__":
    asyncio.run(scrape_acoustic())

if __name__ == "__main__":
    asyncio.run(scrape_acoustic())