import asyncio
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # Added trailing slashes for consistency
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
            # Ensure the base URL ends with a slash
            base_url = cat_url if cat_url.endswith('/') else cat_url + '/'
            print(f"Scanning: {base_url}")
            
            p_num = 1
            while True:
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                try:
                    response = await page.goto(target_url, timeout=60000)
                    
                    if response.status == 404:
                        print(f"   Done. Reached 404 at page {p_num}.")
                        break
                    
                    # Prevent redirect loop
                    if p_num > 1 and page.url.rstrip('/') == base_url.rstrip('/'):
                        break

                    if target_url not in all_final_pages:
                        all_final_pages.append(target_url)
                        print(f"   Success: {target_url}")
                    
                    p_num += 1
                except Exception as e:
                    print(f"   Error: {e}")
                    break

        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            print(f"\nTotal unique pages collected: {len(all_final_pages)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())