import asyncio
import pandas as pd
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_products():
    async with async_playwright() as p:
        # headless=True means the browser window will not appear (faster performance)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            with open('all_pages_to_scrape.txt', 'r', encoding='utf-8') as f:
                # Reading all URLs from the text file
                urls = [line.strip() for line in f.readlines() if line.strip()]
            
            if not urls:
                print("⚠️ Warning: 'all_pages_to_scrape.txt' is empty!")
                return
            print(f"📂 Total pages to process: {len(urls)}")
        except FileNotFoundError:
            print("❌ Error: all_pages_to_scrape.txt not found.")
            return

        all_products = []
        start_time = datetime.now()

        print(f"🚀 Scanning started at {start_time.strftime('%H:%M:%S')}...")

        for index, url in enumerate(urls, 1):
            try:
                # Displaying progress in the terminal
                print(f"🔄 Processing ({index}/{len(urls)}): {url}")
                
                await page.goto(url, timeout=60000)
                # Waiting for the product container to load
                await page.wait_for_selector('.ut2-gl__body', timeout=7000)
                items = await page.query_selector_all('.ut2-gl__body') 

                for item in items:
                    name_elem = await item.query_selector('a.product-title')
                    price_elem = await item.query_selector('.ty-price-num')
                    stock_elem = await item.query_selector('.ty-qty-in-stock')
                    
                    if name_elem and price_elem:
                        name = (await name_elem.inner_text()).strip()
                        raw_price = (await price_elem.inner_text()).strip()
                        
                        # Price cleaning (extracting digits only)
                        try:
                            clean_price = int(''.join(filter(str.isdigit, raw_price)))
                        except:
                            clean_price = 0
                            
                        link = await name_elem.get_attribute('href')
                        
                        # Extracting Product ID
                        price_id_attr = await price_elem.get_attribute('id')
                        product_id = re.findall(r'\d+', price_id_attr)[0] if price_id_attr else "N/A"
                        
                        # Stock status detection
                        stock_text = (await stock_elem.inner_text()).lower() if stock_elem else ""
                        # Detection remains based on the Georgian site text, but the result is English
                        status = "In Stock" if "მარაგშია" in stock_text else "Out of Stock"

                        all_products.append({
                            'Product ID': product_id,
                            'Name': name,
                            'Price (₾)': clean_price,
                            'Status': status,
                            'Link': link,
                            'Last Check': datetime.now().strftime('%Y-%m-%d %H:%M')
                        })
                
                # Intermediate save every 10 pages for safety
                if index % 10 == 0:
                    pd.DataFrame(all_products).to_csv('geovoice_full_inventory.csv', index=False, encoding='utf-8-sig')

            except Exception as e:
                print(f"⚠️ Page {url} skipped due to error: {e}")
                continue 

        # Final save and summary report
        if all_products:
            df = pd.DataFrame(all_products)
            # Remove duplicates based on Product ID
            df.drop_duplicates(subset=['Product ID'], inplace=True)
            df.to_csv('geovoice_full_inventory.csv', index=False, encoding='utf-16')
            
            duration = datetime.now() - start_time
            print("\n" + "="*40)
            print(f"✅ Scanning Completed!")
            print(f"📦 Total unique products collected: {len(df)}")
            print(f"⏱️ Time elapsed: {duration.seconds // 60} minutes")
            print(f"📁 File saved as: geovoice_full_inventory.csv")
            print("="*40)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_products())