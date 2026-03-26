import asyncio
import pandas as pd
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def extract_unique_id(page):
    """
    Extracts UNIQUE_ID with multiple fallback selectors.
    Returns the ID or "N/A" if not found.
    """
    # Add delay to ensure page is fully loaded
    await page.wait_for_timeout(2000)
    
    # Primary selector
    selectors = [
        ".ty-control-group__item",      # Current primary selector
        ".ty-sku-item",                  # First fallback
        "[id^='sku']",                   # ID-based fallback
        ".product-sku",                  # Generic product SKU
        "[data-sku]",                    # Data attribute
        ".sku-value",                    # Alternative class name
        ".product-code",                 # Product code fallback
        "span[class*='sku']",            # Partial class match
    ]
    
    for selector in selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                text = (await element.inner_text()).strip()
                if text and text != "N/A":
                    print(f"         ✅ ID found using selector: {selector}", flush=True)
                    return text
        except Exception as e:
            print(f"         ⚠️ Selector {selector} failed: {str(e)[:30]}", flush=True)
            continue
    
    # If no selector worked, try to extract from page content
    try:
        content = await page.content()
        # Look for SKU/ID patterns in the HTML
        sku_match = re.search(r'[Ss][Kk][Uu][\s:]*([A-Za-z0-9\-]+)', content)
        if sku_match:
            sku_value = sku_match.group(1).strip()
            if sku_value and sku_value != "N/A":
                print(f"         ✅ ID found via regex pattern", flush=True)
                return sku_value
    except:
        pass
    
    print(f"         ❌ No UNIQUE_ID found with any selector", flush=True)
    return "N/A"


async def scrape_geovoice():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"geovoice_inventory_{timestamp}.xlsx"


    try:
        with open('all_pages_to_scrape.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Error: all_pages_to_scrape.txt not found!", flush=True)
        import sys
        sys.exit(1)

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
                            
                            # PRICE - ვიღებთ მხოლოდ ციფრებს
                            raw_price = (await price_el.inner_text()).strip()
                            price = re.sub(r'\D', '', raw_price.split('.')[0])
                            
                            # STATUS
                            status = "In Stock"
                            if "არ არის" in (await item.inner_text()):
                                status = "Out of Stock"

                            # --- UNIQUE_ID-ის ამოღება შიდა გვერდიდან ---
                            unique_id = "N/A"
                            prod_page = await context.new_page()
                            try:
                                await prod_page.goto(full_link, wait_until="domcontentloaded", timeout=25000)
                                
                                # Use helper function with fallback selectors and delay
                                unique_id = await extract_unique_id(prod_page)
                                
                                # დამატებითი შემოწმება სტატუსისთვის (შიდა გვერდი უფრო ზუსტია)
                                inner_content = await prod_page.content()
                                if "მარაგშია" in inner_content or "In Stock" in inner_content:
                                    status = "In Stock"
                                else:
                                    status = "Out of Stock"
                                    
                            except Exception as e:
                                print(f"         ❌ Error extracting product data: {str(e)[:50]}", flush=True)
                                unique_id = "N/A"
                            finally:
                                await prod_page.close()

                            # --- ლოგირება ---
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

                    except Exception as e:
                        print(f"      ⚠️ Skipping item: {str(e)[:50]}", flush=True)
                        continue

                # შუალედური შენახვა ყოველ 5 კატეგორიაში
                if index % 5 == 0:
                    pd.DataFrame(all_data).to_excel(file_name, index=False)

            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}", flush=True)

        await browser.close()

    if all_data:
        df = pd.DataFrame(all_data)
        # ვშლით დუბლიკატებს ID-ის და სახელის მიხედვით
        df.drop_duplicates(subset=['UNIQUE_ID', 'NAME'], keep='first', inplace=True)
        df.to_excel("geovoice_latest_inventory.xlsx", index=False)
        print(f"\n✅ Completed! Collected {len(df)} unique items.")
        print(f"📁 Saved to: geovoice_latest_inventory.xlsx", flush=True)
    else:
        print("\n❌ No data collected.", flush=True)

if __name__ == "__main__":
    asyncio.run(scrape_geovoice())