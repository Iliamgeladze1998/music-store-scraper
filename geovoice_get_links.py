import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        # 🕵️‍♂️ სწორი სინტაქსი stealth რეჟიმისთვის
        await stealth(page)

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

        for base_url in categories:
            print(f"\n🌐 SCANNING: {base_url}", flush=True)
            p_num = 1
            
            while True:
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                # ვასუფთავებთ ქუქიებს ბლოკირების ასარიდებლად
                await context.clear_cookies()
                
                try:
                    # ვიყენებთ "networkidle" რომ გვერდი ბოლომდე დაწყნარდეს
                    response = await page.goto(target_url, wait_until="networkidle", timeout=60000)
                    
                    print(f"📡 Page {p_num} Status: {response.status}", flush=True)

                    if response.status == 404:
                        print(f"🛑 Page {p_num} is 404. Switching category.", flush=True)
                        break

                    # ვამოწმებთ არის თუ არა პროდუქტები
                    products = await page.query_selector_all(".product-item, .ty-column4")
                    
                    if len(products) > 0:
                        all_final_pages.append(target_url)
                        print(f"✅ Success: Page {p_num} ({len(products)} products found)", flush=True)
                        p_num += 1
                        # 🚶‍♂️ პაუზა, რომ არ დავიბლოკოთ
                        await asyncio.sleep(3) 
                    else:
                        print(f"📭 Empty/End. Moving to next category.", flush=True)
                        break

                except Exception as e:
                    print(f"❌ Error at {target_url}: {e}", flush=True)
                    break

        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())