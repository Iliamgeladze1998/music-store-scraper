import asyncio
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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
            print(f"\n🌐 --- CATEGORY START: {base_url} ---", flush=True)
            p_num = 1
            
            while True:
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                print(f"🔗 [Step 1] Requesting URL: {target_url}", flush=True)
                
                try:
                    # ვაგზავნით მოთხოვნას და ველოდებით მხოლოდ პირველ პასუხს
                    response = await page.goto(target_url, wait_until="commit", timeout=30000)
                    
                    status = response.status if response else "NO_RESPONSE"
                    print(f"📡 [Step 2] Server Response Status: {status}", flush=True)

                    if status == 404:
                        print(f"🛑 [Result] 404 Error! No more pages here.", flush=True)
                        break
                    
                    if status == 403:
                        print(f"🚫 [Result] 403 Forbidden! GitHub is blocked. Trying to wait 5s...", flush=True)
                        await asyncio.sleep(5)
                        # არ გავჩერდეთ, ვცადოთ მაინც კონტენტის შემოწმება
                    
                    # ველოდებით შენს მიერ ნაპოვნ "მთავარ კონტეინერს"
                    # ვიყენებთ შენს სურათზე არსებულ კლასს .main-content-grid
                    print(f"⏳ [Step 3] Waiting for main content grid (.main-content-grid)...", flush=True)
                    try:
                        await page.wait_for_selector(".main-content-grid", timeout=8000)
                        print(f"✅ [Step 4] Main grid found on screen.", flush=True)
                    except:
                        print(f"⚠️ [Step 4] Grid NOT found after 8s. Checking products...", flush=True)

                    # ვამოწმებთ არის თუ არა პროდუქტები
                    products = await page.query_selector_all(".product-item, .ty-column4")
                    p_count = len(products)
                    print(f"📦 [Step 5] Product count on page: {p_count}", flush=True)

                    if p_count > 0:
                        all_final_pages.append(target_url)
                        print(f"⭐ [Success] Page {p_num} added to list.", flush=True)
                        p_num += 1
                        # მცირე პაუზა შემდეგ გვერდამდე
                        await asyncio.sleep(1)
                    else:
                        print(f"📭 [Result] Page {p_num} has no products. Category ends.", flush=True)
                        break

                except Exception as e:
                    print(f"❌ [Error] Something went wrong: {str(e)[:100]}", flush=True)
                    break

        # ფაილში შენახვა
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            print(f"\n📊 --- SCAN COMPLETE ---")
            print(f"Total pages collected: {len(all_final_pages)}", flush=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())