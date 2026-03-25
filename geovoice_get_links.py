import asyncio
import sys
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        # ინიციალიზაცია
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

        for cat_url in categories:
            base_url = cat_url if cat_url.endswith('/') else cat_url + '/'
            print(f"\n🚀 Scanning Category: {base_url}", flush=True)
            
            p_num = 1
            while True:
                # ლინკის აწყობა (გვერდი 1 არის მთავარი, დანარჩენი /page-X/)
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                success = False
                for attempt in range(2):
                    try:
                        # 1. გადასვლა გვერდზე
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                        
                        # 2. მთავარი "მუხრუჭი": ველოდებით პროდუქტების ან 404-ის გამოჩენას
                        # ეს აიძულებს სკრიპტს დაელოდოს საიტს (მაქსიმუმ 8 წამი)
                        try:
                            await page.wait_for_selector(".product-item, .ty-column4, .ty-exception", timeout=8000)
                        except:
                            pass 

                        # 3. მცირე პაუზა საბოლოო დარწმუნებისთვის
                        await asyncio.sleep(1.5)
                        success = True
                        break 
                    except Exception as e:
                        if attempt == 0:
                            print(f"   ⚠️ Page {p_num} slow... Retrying (Attempt 2)", flush=True)
                            await asyncio.sleep(2)
                        else:
                            print(f"   ❌ Page {p_num} failed after 2 attempts", flush=True)

                if not success:
                    break

                # კონტენტის აღება შემოწმებისთვის
                content = await page.content()
                
                # 🛠️ ლოგიკა 1: 404-ის დაფიქსირება (შენი სურათის მიხედვით)
                # თუ გვერდზე არის 404-ის კლასი ან ტექსტი, ვჩერდებით
                if "ty-exception" in content or "404" in content:
                    print(f"   🛑 Page {p_num} is 404/Not Found. Moving to next category.", flush=True)
                    break

                # 🛠️ ლოგიკა 2: პროდუქტების არსებობა
                # თუ დაველოდეთ და მაინც არაფერია, ე.ი. კატეგორია მორჩა
                products = await page.query_selector_all(".product-item, .ty-column4")
                if len(products) == 0:
                    print(f"   📭 Page {p_num} is empty. Finishing category.", flush=True)
                    break

                # 🛠️ ლოგიკა 3: Redirect-ის დაზღვევა
                if p_num > 1 and page.url.rstrip('/') == base_url.rstrip('/'):
                    print(f"   🔄 Redirect detected (Back to Page 1). Stopping.", flush=True)
                    break

                # თუ გვერდი ვალიდურია, ვინახავთ
                if target_url not in all_final_pages:
                    all_final_pages.append(target_url)
                    print(f"   ✅ Success: Page {p_num}", flush=True)
                
                p_num += 1

        # შედეგის შენახვა ფაილში
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            print(f"\n📊 TOTAL UNIQUE PAGES COLLECTED: {len(all_final_pages)}", flush=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())