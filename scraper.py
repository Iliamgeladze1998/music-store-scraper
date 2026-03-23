import pandas as pd
from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime

def scrape_acoustic_full():
    # 🎯 ფაილის სახელისთვის დრო
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"acoustic_inventory_{timestamp}.xlsx"

    # 1. ლინკების წაკითხვა (რომ ყველაფერს გადაუაროს)
    try:
        with open("subcategory_links.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("❌ ფაილი subcategory_links.txt ვერ მოიძებნა!")
        return

    all_data = []

    with sync_playwright() as p:
        # headless=False რომ დაინახო პროცესი. თუ გინდა უფრო სწრაფი იყოს, შეცვალე True-თი
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        for index, base_url in enumerate(urls, 1):
            print(f"\n🚀 ({index}/{len(urls)}) ვამუშავებ კატეგორიას: {base_url}")
            
            try:
                page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ ვერ შევედი ლინკზე: {base_url}. გამოვტოვებ...")
                continue

            page_num = 1
            while True:
                print(f"   📄 გვერდი {page_num}")
                
                # ბოლომდე ჩასვლა, რომ Lazy Load ელემენტები გამოჩნდეს
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                # პროდუქტის ბლოკების მოძებნა
                products = page.query_selector_all(".ty-compact-list__content")
                
                if not products:
                    # თუ კომპაქტური ლისტი არ არის, ვცადოთ ჩვეულებრივი გრიდი
                    products = page.query_selector_all(".ty-column4")

                for product in products:
                    try:
                        name_el = product.query_selector("a.product-title")
                        if not name_el: continue
                        
                        name = name_el.inner_text().strip()
                        link = name_el.get_attribute("href")

                        # Product ID
                        id_el = product.query_selector("[id^='price_update_']")
                        product_id = id_el.get_attribute("id").replace("price_update_", "") if id_el else "N/A"

                        # Price (₾) - შენი იდეალური ლოგიკა
                        price_val = "0"
                        price_container = product.query_selector(".ty-price")
                        if price_container:
                            raw_text = price_container.inner_text().strip()
                            digits = "".join(re.findall(r'\d+', raw_text))
                            if digits.endswith("00") and len(digits) > 2:
                                price_val = digits[:-2]
                            else:
                                price_val = digits

                        # Status
                        status = "In Stock"
                        if "არ არის" in product.inner_text():
                            status = "Out of Stock"

                        all_data.append({
                            'Product ID': product_id,
                            'Name': name,
                            'Price (₾)': price_val,
                            'Status': status,
                            'Link': link,
                            'Last Check': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                    except:
                        continue

                # 🎯 შემდეგ გვერდზე გადასვლა
                # ვამოწმებთ "Next" ღილაკს და ასევე ვამოწმებთ, რომ ის ნამდვილად კლიკებადია
                next_btn = page.query_selector("a.ty-pagination__next")
                if next_btn and next_btn.is_visible():
                    try:
                        next_btn.click()
                        page_num += 1
                        # ველოდებით ახალი გვერდის ჩატვირთვას
                        time.sleep(4) 
                    except:
                        break
                else:
                    break

        browser.close()

    # საბოლოო შენახვა
    if all_data:
        df = pd.DataFrame(all_data)
        # დუბლიკატების მოცილება ID-ს მიხედვით
        df.drop_duplicates(subset=['Product ID'], inplace=True)
        
        df.to_excel(file_name, index=False, engine='xlsxwriter')
        print(f"\n✅ დასრულდა! სულ შეგროვდა {len(all_data)} უნიკალური ნივთი.")
        print(f"📁 ფაილი შენახულია: {file_name}")
    else:
        print("❌ მონაცემები ვერ მოიძებნა.")

if __name__ == "__main__":
    scrape_acoustic_full()