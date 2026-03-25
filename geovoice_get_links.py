import asyncio
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        # ვიყენებთ Chromium-ს
        browser = await p.chromium.launch(headless=True)
        
        # ვქმნით კონტექსტს "ადამიანური" პარამეტრებით
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9,ka;q=0.8",
                "Referer": "https://geovoice.ge/"
            }
        )
        
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

        for base_url in categories:
            print(f"\n🌐 SCANNING: {base_url}", flush=True)
            p_num = 1
            
            while True:
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                try:
                    # ყოველ რექვესთზე ვასუფთავებთ ქუქიებს
                    await context.clear_cookies()
                    
                    # შევდივართ გვერდზე
                    response = await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                    
                    print(f"📡 Page {p_num} Status: {response.status}", flush=True)

                    if response.status == 404:
                        print(f"🛑 Page {p_num} is 404. Category finished.", flush=True)
                        break

                    # ველოდებით ცოტას, რომ ეკრანი დაწყნარდეს
                    await asyncio.sleep(2.5)

                    # ვამოწმებთ პროდუქტების არსებობას
                    products = await page.query_selector_all(".product-item, .ty-column4")
                    
                    if len(products) > 0:
                        if target_url not in all_final_pages:
                            all_final_pages.append(target_url)
                        print(f"✅ Success: Page {p_num} - Found {len(products)} products", flush=True)
                        p_num += 1
                        # 🚶‍♂️ უფრო გრძელი პაუზა "ადამიანურობისთვის"
                        await asyncio.sleep(3) 
                    else:
                        print(f"📭 Empty page. Category ends.", flush=True)
                        break

                except Exception as e:
                    print(f"❌ Error at {target_url}: {str(e)[:50]}", flush=True)
                    break

        # შენახვა
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())