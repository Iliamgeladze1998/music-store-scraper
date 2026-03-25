import pandas as pd
from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime

def scrape_acoustic():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"acoustic_inventory_{timestamp}.xlsx"

    try:
        with open("subcategory_links.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        
        if not urls:
            print("Error: subcategory_links.txt is empty!")
            return
            
        print(f"--- Starting Full Scrape: {len(urls)} categories found ---")
            
    except FileNotFoundError:
        print("Error: subcategory_links.txt not found!")
        return

    all_data = []

    with sync_playwright() as p:
        # Headless=True დავაყენე სისწრაფისთვის, თუ პრობლემა იქნება შეცვალე False-ზე
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        for index, url in enumerate(urls, 1):
            try:
                print(f"[{index}/{len(urls)}] Processing: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # ვაცადოთ გვერდს ჩატვირთვა და ჩამოვსქროლოთ ბოლომდე
                time.sleep(2)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                products = page.query_selector_all(".ty-column4, .ty-compact-list__content")
                
                for product in products:
                    try:
                        name_el = product.query_selector("a.product-title")
                        if not name_el: continue
                        
                        name = name_el.inner_text().strip()
                        link = name_el.get_attribute("href")

                        # UNIQUE_ID (SKU) ამოღება
                        sku_el = product.query_selector("[id^='product_code_']")
                        unique_id = sku_el.inner_text().strip() if sku_el else "N/A"

                        # ფასის ამოღება და გასუფთავება
                        price_val = "0"
                        price_container = product.query_selector(".ty-price")
                        if price_container:
                            raw_text = price_container.inner_text().strip()
                            digits = "".join(re.findall(r'\d+', raw_text))
                            # ვაკორექტირებთ თუ ფასი თეთრებშია (მაგ: 120000 -> 1200)
                            if digits.endswith("00") and len(digits) > 2:
                                price_val = digits[:-2]
                            else:
                                price_val = digits

                        # მარაგის სტატუსი
                        status = "In Stock"
                        if "არ არის" in product.inner_text():
                            status = "Out of Stock"

                        all_data.append({
                            'UNIQUE_ID': unique_id,
                            'NAME': name,
                            'PRICE': price_val,
                            'STATUS': status,
                            'LINK': link,
                            'DATE': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                    except Exception:
                        continue
                
                # ყოველ 10 კატეგორიაში ერთხელ შევინახოთ შუალედური ვერსია (დაზღვევისთვის)
                if index % 10 == 0:
                    pd.DataFrame(all_data).to_excel(file_name, index=False)

            except Exception as e:
                print(f"Skipping category {url} due to error: {e}")
                continue

        browser.close()

    if all_data:
        df = pd.DataFrame(all_data)
        # ვშლით დუბლიკატებს UNIQUE_ID-ის მიხედვით
        df.drop_duplicates(subset=['UNIQUE_ID'], keep='first', inplace=True)
        df.to_excel(file_name, index=False)
        print(f"\n✅ Completed! Collected {len(df)} unique items.")
        print(f"File saved: {file_name}")
    else:
        print("No data collected.")

if __name__ == "__main__":
    scrape_acoustic()