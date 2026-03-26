import asyncio
import pandas as pd
import re
from datetime import datetime
from playwright.async_api import async_playwright, Route

async def block_unnecessary_resources(route: Route):
    """Block images, CSS, fonts, and analytics to speed up loading."""
    url = route.request.url
    # Block these resource types
    if any(ext in url for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.woff', '.woff2', '.ttf', '.css', 'analytics', 'gtag', 'tracking']):
        await route.abort()
    else:
        await route.continue_()


async def extract_products_from_page(page, url):
    """
    Extracts all products from a single page.
    Returns list of product dictionaries.
    """
    products_data = []
    
    try:
        # Navigate with resource blocking
        await page.route("**/*", block_unnecessary_resources)
        
        response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        
        if response.status != 200:
            print(f"   ⚠️ HTTP {response.status}", flush=True)
            return products_data
        
        # Wait for product elements with shorter timeout
        try:
            await page.wait_for_selector(".ty-column4, .ty-compact-list__content", timeout=5000)
        except:
            pass  # Continue even if selector not found
        
        # Scroll to load all content (but with timeout)
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)  # Reduced from 2 seconds
        except:
            pass
        
        # Extract products
        products = await page.query_selector_all(".ty-column4, .ty-compact-list__content")
        
        for product in products:
            try:
                # Safely extract elements
                name_el = await product.query_selector("a.product-title")
                if not name_el:
                    continue
                
                name = (await name_el.inner_text()).strip()
                link = await name_el.get_attribute("href")
                
                # UNIQUE_ID with fallback selectors
                unique_id = "N/A"
                sku_selectors = [
                    "[id^='product_code_']",
                    ".product-code",
                    "[data-sku]",
                    ".sku-value"
                ]
                
                for selector in sku_selectors:
                    try:
                        sku_el = await product.query_selector(selector)
                        if sku_el:
                            unique_id = (await sku_el.inner_text()).strip()
                            break
                    except:
                        continue
                
                # Price extraction
                price_val = "0"
                try:
                    price_container = await product.query_selector(".ty-price")
                    if price_container:
                        raw_text = (await price_container.inner_text()).strip()
                        digits = "".join(re.findall(r'\d+', raw_text))
                        
                        # Correct price if in hundreds (120000 -> 1200)
                        if digits.endswith("00") and len(digits) > 2:
                            price_val = digits[:-2]
                        else:
                            price_val = digits
                except:
                    pass
                
                # Status
                status = "In Stock"
                try:
                    product_text = await product.inner_text()
                    if "არ არის" in product_text or "Out of Stock" in product_text:
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
                continue
        
        print(f"   ✅ Found {len(products_data)} products", flush=True)
        
    except asyncio.TimeoutError:
        print(f"   ⏱️ Timeout loading {url}", flush=True)
    except Exception as e:
        print(f"   ⚠️ Error: {str(e)[:40]}", flush=True)
    
    return products_data


async def scrape_acoustic():
    """
    Optimized async version with parallel page processing.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"acoustic_inventory_{timestamp}.xlsx"
    
    start_time = datetime.now()

    try:
        with open("subcategory_links.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        
        if not urls:
            print("❌ Error: subcategory_links.txt is empty!")
            return
            
        print(f"🚀 Starting scrape: {len(urls)} categories found\n", flush=True)
            
    except FileNotFoundError:
        print("❌ Error: subcategory_links.txt not found!")
        return

    all_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},  # Smaller viewport
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # Create a pool of 5 concurrent pages for better throughput
        max_concurrent = 5
        pages = [await context.new_page() for _ in range(max_concurrent)]
        
        try:
            # Process URLs in batches with concurrent pages
            tasks = []
            for i, url in enumerate(urls):
                page = pages[i % len(pages)]  # Round-robin assignment
                print(f"[{i+1}/{len(urls)}] {url.split('/')[-2]}", flush=True)
                task = extract_products_from_page(page, url)
                tasks.append(task)
            
            # Gather all results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten and process results
            for result in results:
                if isinstance(result, list):
                    all_data.extend(result)
                elif isinstance(result, Exception):
                    print(f"⚠️ Task error: {result}", flush=True)
            
        finally:
            # Clean up pages
            for page in pages:
                try:
                    await page.close()
                except:
                    pass
            await browser.close()

    # Save to Excel with deduplication
    if all_data:
        df = pd.DataFrame(all_data)
        
        # Remove duplicates by UNIQUE_ID, keep first
        df.drop_duplicates(subset=['UNIQUE_ID'], keep='first', inplace=True)
        
        df.to_excel(file_name, index=False)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*50}")
        print(f"✅ COMPLETE!")
        print(f"   📊 Total items: {len(df)}")
        print(f"   ⏱️  Time: {elapsed:.1f}s ({elapsed/len(urls):.1f}s per category)")
        print(f"   📁 Saved: {file_name}")
        print(f"{'='*50}\n", flush=True)
    else:
        print("\n❌ No data collected.", flush=True)


if __name__ == "__main__":
    asyncio.run(scrape_acoustic())