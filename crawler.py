import asyncio
import pandas as pd
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_geovoice():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"geovoice_inventory_{timestamp}.xlsx"

    try:
        if not os.path.exists('all_pages_to_scrape.txt'):
            print("Error: all_pages_to_scrape.txt not found.")
            return

        with open('all_pages_to_scrape.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        
        if not urls:
            print("Error: all_pages_to_scrape.txt is empty!")
            return
            
        print(f"--- Starting Full Scrape: {len(urls)} categories found ---")
            
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    all_products = []
    
    async with async_playwright() as p:
        # headless=True უფრო სწრაფია, False-ს თუ დააყენებ დაინახავ პროცესს
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        for index, url in enumerate(urls, 1):
            try:
                print(f"[{index}/{len(urls)}] Processing category: {url}")
                await page.goto(url, timeout=60000)
                
                # ველოდებით პროდუქტების გამოჩენას
                try:
                    await page.wait_for_selector('.ut2-gl__body', timeout=10000)
                except:
                    print(f"No products found on page: {url}")
                    continue

                items = await page.query_selector_all('.ut2-gl__body') 

                for item in items:
                    name_elem = await item.query_selector('a.product-title')
                    price_elem = await item.query_selector('.ty-price-num')
                    
                    if name_elem and price_elem:
                        name = (await name_elem.inner_text()).strip()
                        link = await name_elem.get_attribute('href')
                        
                        # შევდივართ პროდუქტის შიგნით UNIQUE_ID-ის ასაღებად
                        prod_page = await context.new_page()
                        try:
                            await prod_page.goto(link, timeout=30000)
                            # ვიღებთ SKU კოდს (მაგ: 935111)
                            sku_el = await prod_page.query_selector("[id^='product_code_']")
                            unique_id = (await sku_el.inner_text()).strip() if sku_el else "N/A"
                            await prod_page.close()
                        except:
                            unique_id = "N/A"
                            await prod_page.close()

                        raw_price = (await price_elem.inner_text()).strip()
                        clean_price = "".join(filter(str.isdigit, raw_price))
                        
                        status = "In Stock"
                        item_html = await item.inner_text()
                        if "არ არის" in item_html:
                            status = "Out of Stock"

                        all_products.append({
                            'UNIQUE_ID': unique_id,
                            'NAME': name,
                            'PRICE': clean_price,
                            'STATUS': status,
                            'LINK': link,
                            'DATE': datetime.now().strftime('%Y-%m-%d %H:%M')
                        })

                # ყოველ 5 კატეგორიაში ერთხელ ვინახავთ მონაცემებს დაზღვევისთვის
                if index % 5 == 0:
                    pd.DataFrame(all_products).to_excel(file_name, index=False)

            except Exception as e:
                print(f"Skipping {url} due to error: {e}")
                continue

        await browser.close()

    if all_products:
        df = pd.DataFrame(all_products)
        # ვშლით დუბლიკატებს ID-ის მიხედვით
        df.drop_duplicates(subset=['UNIQUE_ID'], keep='first', inplace=True)
        df.to_excel(file_name, index=False)
        print(f"\n✅ Completed! Collected {len(df)} products from Geovoice.")
        print(f"File saved: {file_name}")
    else:
        print("No products found.")

if __name__ == "__main__":
    asyncio.run(scrape_geovoice())