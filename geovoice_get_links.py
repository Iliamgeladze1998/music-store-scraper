import asyncio
import sys
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        categories = [
            "https://geovoice.ge/audio/",
            "https://geovoice.ge/dj-studia/",
            "https://geovoice.ge/video-aparatura/",
            "https://geovoice.ge/sasce-ganat-aparatura/",
            "https://geovoice.ge/komutacia-kabel-adampt-konector/",
            "https://geovoice.ge/sadgamebi-sakidebi-aksesuarebi/",
            "https://geovoice.ge/sadgamebi-sakidebi/" 
        ]
        
        all_final_pages = []

        for cat_url in categories:
            base_url = cat_url if cat_url.endswith('/') else cat_url + '/'
            print(f"\n🚀 Scanning Category: {base_url}", flush=True)
            
            p_num = 1
            while True:
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                try:
                    await page.goto(target_url, wait_until="networkidle", timeout=60000)
                    
                    # 1. მთავარი მუხრუჭი: ვამოწმებთ 404-ს პირდაპირ ტექსტში
                    # ეს დაიჭერს იმას, რაც შენს სურათზეა (image_c1c6a2.png)
                    content = await page.content()
                    error_box = await page.query_selector(".ty-exception, .ty-exception_code")
                    
                    if error_box or "404" in content or "ვერ იქნა მოძიებული" in content:
                        print(f"🛑 Found Visual 404 at page {p_num}. KILLING LOOP.", flush=True)
                        break

                    # 2. დაზღვევა: ვამოწმებთ არის თუ არა პროდუქტები
                    products = await page.query_selector_all(".product-item, .ty-column4")
                    if len(products) == 0:
                        print(f"📭 Page {p_num} is empty. Finishing category.", flush=True)
                        break

                    if target_url not in all_final_pages:
                        all_final_pages.append(target_url)
                        print(f"✅ Success: Page {p_num}", flush=True)
                    
                    p_num += 1
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"❌ Error at page {p_num}: {e}", flush=True)
                    break

        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())