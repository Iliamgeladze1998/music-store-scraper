import asyncio
import sys
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # ვამატებთ რეალურ User-Agent-ს, რომ საიტმა ბოტად არ ჩაგვთვალოს
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                success = False
                for attempt in range(2):  # 2 მცდელობა თითო გვერდზე
                    try:
                        # domcontentloaded გაცილებით სწრაფია და სტაბილური
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                        # პატარა პაუზა, რომ HTML-მა "დაალაგოს" პროდუქტები
                        await asyncio.sleep(1.5)
                        success = True
                        break 
                    except Exception as e:
                        if attempt == 0:
                            print(f"   ⚠️ Page {p_num} slow... Retrying (Attempt 2)", flush=True)
                        else:
                            print(f"   ❌ Page {p_num} failed after 2 attempts: {e}", flush=True)

                if not success:
                    # თუ გვერდი 2-ჯერაც ვერ ჩაიტვირთა, ვასრულებთ ამ კატეგორიას
                    break

                # --- შემოწმების ეტაპი ---
                content = await page.content()
                error_box = await page.query_selector(".ty-exception, .ty-exception_code")
                
                # 1. ვამოწმებთ 404-ს (შენი სურათის მიხედვით)
                if error_box or "404" in content or "ვერ იქნა მოძიებული" in content:
                    print(f"   🛑 Found Visual 404 at page {p_num}. Switching category.", flush=True)
                    break

                # 2. ვამოწმებთ არის თუ არა პროდუქტები
                products = await page.query_selector_all(".product-item, .ty-column4")
                if len(products) == 0:
                    print(f"   📭 Page {p_num} is empty. Finishing.", flush=True)
                    break

                # 3. Redirect შემოწმება
                if p_num > 1 and page.url.rstrip('/') == base_url.rstrip('/'):
                    print(f"   🔄 Redirected to start. Ending category.", flush=True)
                    break

                # თუ ყველაფერი კარგადაა, ვამატებთ სიას
                if target_url not in all_final_pages:
                    all_final_pages.append(target_url)
                    print(f"   ✅ Success: Page {p_num}", flush=True)
                
                p_num += 1

        # ფაილში შენახვა
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            print(f"\n📊 Total unique pages collected: {len(all_final_pages)}", flush=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())