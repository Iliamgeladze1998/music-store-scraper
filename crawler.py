
import pandas as pd
import re
from datetime import datetime
import asyncio
import logging
from base_scraper import BaseScraper
from config import GEOVOICE_SELECTORS, SCRAPER_CONFIG

class GeovoiceScraper(BaseScraper):
    def __init__(self, logger=None):
        super().__init__(GEOVOICE_SELECTORS, logger=logger)

    async def process_page(self, page, url):
        products_data = []
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            if not response or response.status != 200:
                self.logger.warning(f"⚠️ HTTP {getattr(response, 'status', 'N/A')} for {url}")
                return products_data
            try:
                await page.wait_for_selector(self.selectors['product_container'], timeout=5000)
            except:
                pass
            products = await page.query_selector_all(self.selectors['product_container'])
            for product in products:
                try:
                    name_el = await product.query_selector(self.selectors['name'])
                    if not name_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    link = await name_el.get_attribute("href")
                    unique_id = "N/A"
                    for selector in self.selectors['sku']:
                        try:
                            sku_el = await product.query_selector(selector)
                            if sku_el:
                                unique_id = (await sku_el.inner_text()).strip()
                                break
                        except:
                            continue
                    price_val = "0"
                    try:
                        price_container = await product.query_selector(self.selectors['price'])
                        if price_container:
                            raw_text = (await price_container.inner_text()).strip()
                            digits = "".join(re.findall(r'\d+', raw_text))
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
            self.logger.info(f"✅ Found {len(products_data)} products at {url}")
        except asyncio.TimeoutError:
            self.logger.warning(f"⏱️ Timeout loading {url}")
        except Exception as e:
            self.logger.warning(f"⚠️ Error: {str(e)[:40]} at {url}")
        return products_data


async def scrape_geovoice():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    async def scrape_geovoice():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        file_name = f"geovoice_inventory_{timestamp}.xlsx"
        try:
            with open("all_pages_to_scrape.txt", "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f.readlines() if line.strip()]
            if not urls:
                print("❌ Error: all_pages_to_scrape.txt is empty!")
                return
            print(f"🚀 Starting scrape: {len(urls)} categories found\n", flush=True)
        except FileNotFoundError:
            print("❌ Error: all_pages_to_scrape.txt not found!")
            import sys
            sys.exit(1)
        logger = logging.getLogger("geovoice")
        scraper = GeovoiceScraper(logger=logger)
        all_data = []
        results = await scraper.run(urls, scraper.process_page)
        for batch in results:
            if batch:
                all_data.extend(batch)
        if all_data:
            df = pd.DataFrame(all_data)
            df.drop_duplicates(subset=['UNIQUE_ID'], keep='first', inplace=True)
            df.to_excel(file_name, index=False)
            print(f"\n✅ COMPLETE! {len(df)} items scraped and saved to {file_name}")
        else:
            print("\n❌ No data collected.", flush=True)

    if __name__ == "__main__":
        asyncio.run(scrape_geovoice())