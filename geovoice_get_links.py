import asyncio
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        # headless=True აუცილებელია GitHub-ისთვის
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
            print(f"🚀 Scanning Category: {base_url}")
            
            p_num = 1
            while True:
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                try:
                    # 60 წამიანი ლოდინი, რომ ნელ საიტზეც იმუშაოს
                    response = await page.goto(target_url, wait_until="networkidle", timeout=60000)
                    
                    # 1. შემოწმება სტატუს კოდით
                    if response.status == 404:
                        print(f"   🛑 Reached 404 at page {p_num}. Switching category...")
                        break
                    
                    # 2. შემოწმება რეალურ შინაარსზე (მთავარი "მუხრუჭი")
                    # ვეძებთ პროდუქტის ელემენტს (Geovoice-ზე ეს არის 'product-item' ან 'ty-column4')
                    products = await page.query_selector_all(".product-item, .ty-column4")
                    
                    if len(products) == 0:
                        print(f"   📭 Page {p_num} is empty. No more products here.")
                        break

                    # 3. Redirect-ის დაზღვევა
                    if p_num > 1 and page.url.rstrip('/') == base_url.rstrip('/'):
                        print(f"   🔄 Redirected to first page. Category finished.")
                        break

                    if target_url not in all_final_pages:
                        all_final_pages.append(target_url)
                        print(f"   ✅ Success: Page {p_num}")
                    
                    p_num += 1
                    # მცირე პაუზა სერვერის "დასასვენებლად"
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"   ❌ Error at {target_url}: {e}")
                    break

        # ფაილში შენახვა
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            print(f"\n📊 Total unique pages collected: {len(all_final_pages)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())