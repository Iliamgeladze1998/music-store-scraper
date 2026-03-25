import asyncio
import pandas as pd
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_geovoice():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"geovoice_inventory_{timestamp}.xlsx"

    if not os.path.exists('all_pages_to_scrape.txt'):
        print("❌ Error: all_pages_to_scrape.txt not found!", flush=True)
        return

    with open('all_pages_to_scrape.txt', 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        print("❌ Error: all_pages_to_scrape.txt is empty!", flush=True)
        return

    print(f"\n--- 🚀 Starting Full Scrape: {len(urls)} categories found ---", flush=True)
    all_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        main_page = await context.new_page()

        for index, url in enumerate(urls, 1):
            print(f"\n🌐 [{index}/{len(urls)}] Processing: {url}", flush=True)
            try:
                await main_page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)

                items = await main_page.query_selector_all(".ut2-gl__body, .product-item")
                
                for item in items:
                    try:
                        name_el = await item.query_selector("a.product-title")
                        price_el = await item.query_selector(".ty-price-num")
                        
                        if name_el and price_el:
                            name = (await name_el.inner_text()).strip()
                            raw_link = await name_el.get_attribute("href")
                            full_link = raw_link if raw_link.startswith('http') else f"https://geovoice.ge{raw_link}"
                            
                            raw_price = (await price_el.inner_text()).strip()
                            price = "".join(filter(str.isdigit, raw_price))
                            
                            # სტატუსი ინგლისურად (როგორც Acoustic-ში)
                            status = "In Stock"
                            if "არ არის" in (await item.inner_text()):
                                status = "Out of Stock"

                            # UNIQUE_ID შიდა გვერდიდან
                            unique_id = "N/A"
                            prod_page = await context.new_page()
                            try:
                                await prod_page.goto(full_link, wait_until="domcontentloaded", timeout=25000)
                                sku_selector = "span[id^='product_code_']"
                                await prod_page.wait_for_selector(sku_selector, timeout=6000)
                                sku_el = await prod_page.query_selector(sku_selector)
                                if sku_el:
                                    unique_id = (await sku_el.inner_text()).strip()
                            except:
                                unique_id = "N/A"
                            finally:
                                await prod_page.close()

                            # --- ლოგირება: ზუსტად Acoustic-ის პრინტის სტილი ---
                            print(f"      ---------------------------------------------")
                            print(f"      🆔 UNIQUE_ID: {unique_id}")
                            print(f"      📦 NAME: {name}")
                            print(f"      💰 PRICE: {price} GEL")
                            print(f"      🏷️ STATUS: {status}")
                            print(f"      🔗 LINK: {full_link}")

                            all_data.append({
                                'UNIQUE_ID': unique_id,
                                'NAME': name,
                                'PRICE': price,
                                'STATUS': status,
                                'LINK': full_link,
                                'DATE': datetime.now().strftime('%Y-%m-%d %H:%M')
                            })

                    except Exception:
                        continue

                if index % 5 == 0:
                    pd.DataFrame(all_data).to_excel(file_name, index=False)

            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}", flush=True)

        await browser.close()

    if all_data:
        df = pd.DataFrame(all_data)
        df.drop_duplicates(subset=['UNIQUE_ID', 'NAME'], keep='first', inplace=True)
        df.to_excel("geovoice_latest_inventory.xlsx", index=False)
        print(f"\n✅ Completed! Collected {len(df)} unique items.")
    else:
        print("\n❌ No data collected.")

if __name__ == "__main__":
    asyncio.run(scrape_geovoice())