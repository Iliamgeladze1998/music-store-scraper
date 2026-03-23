import asyncio
import pandas as pd
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_products():
    async with async_playwright() as p:
        # headless=True ნიშნავს, რომ ბრაუზერის ფანჯარა არ გამოჩნდება (უფრო სწრაფია)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            with open('all_pages_to_scrape.txt', 'r', encoding='utf-8') as f:
                # აქ მოვხსენი [:1], ახლა წაიკითხავს აბსოლუტურად ყველა ლინკს
                urls = [line.strip() for line in f.readlines() if line.strip()]
            
            if not urls:
                print("⚠️ ფაილი 'all_pages_to_scrape.txt' ცარიელია!")
                return
            print(f"📂 სულ დასამუშავებელია {len(urls)} გვერდი.")
        except FileNotFoundError:
            print("❌ შეცდომა: all_pages_to_scrape.txt ვერ მოიძებნა.")
            return

        all_products = []
        start_time = datetime.now()

        print(f"🚀 სკანირება დაიწყო {start_time.strftime('%H:%M:%S')}-ზე...")

        for index, url in enumerate(urls, 1):
            try:
                # ტერმინალში გამოვიტანოთ პროგრესი, რომ არ მოგვეწყინოს ლოდინისას
                print(f"🔄 მუშავდება ({index}/{len(urls)}): {url}")
                
                await page.goto(url, timeout=60000)
                # ველოდებით პროდუქტების კონტეინერს
                await page.wait_for_selector('.ut2-gl__body', timeout=7000)
                items = await page.query_selector_all('.ut2-gl__body') 

                for item in items:
                    name_elem = await item.query_selector('a.product-title')
                    price_elem = await item.query_selector('.ty-price-num')
                    stock_elem = await item.query_selector('.ty-qty-in-stock')
                    
                    if name_elem and price_elem:
                        name = (await name_elem.inner_text()).strip()
                        raw_price = (await price_elem.inner_text()).strip()
                        
                        # ფასის გასუფთავება (მხოლოდ ციფრები)
                        try:
                            clean_price = int(''.join(filter(str.isdigit, raw_price)))
                        except:
                            clean_price = 0
                            
                        link = await name_elem.get_attribute('href')
                        
                        # ID-ის ამოღება
                        price_id_attr = await price_elem.get_attribute('id')
                        product_id = re.findall(r'\d+', price_id_attr)[0] if price_id_attr else "N/A"
                        
                        # მარაგის სტატუსი
                        stock_text = (await stock_elem.inner_text()).lower() if stock_elem else ""
                        status = "In Stock" if "მარაგშია" in stock_text else "Out of Stock"

                        all_products.append({
                            'Product ID': product_id,
                            'Name': name,
                            'Price (₾)': clean_price,
                            'Status': status,
                            'Link': link,
                            'Last Check': datetime.now().strftime('%Y-%m-%d %H:%M')
                        })
                
                # ყოველ 10 გვერდზე ერთხელ შევინახოთ შუალედური შედეგი (დაზღვევისთვის)
                if index % 10 == 0:
                    pd.DataFrame(all_products).to_csv('geovoice_full_inventory.csv', index=False, encoding='utf-8-sig')

            except Exception as e:
                print(f"⚠️ გვერდი {url} გამოტოვებულია: {e}")
                continue 

        # საბოლოო შენახვა და რეპორტი
        if all_products:
            df = pd.DataFrame(all_products)
            df.drop_duplicates(subset=['Product ID'], inplace=True)
            df.to_csv('geovoice_full_inventory.csv', index=False, encoding='utf-8-sig')
            
            duration = datetime.now() - start_time
            print("\n" + "="*40)
            print(f"✅ სკანირება დასრულდა!")
            print(f"📦 სულ შეგროვდა: {len(df)} პროდუქტი")
            print(f"⏱️ დახარჯული დრო: {duration.seconds // 60} წუთი")
            print(f"📁 ფაილი: geovoice_full_inventory.csv")
            print("="*40)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_products())