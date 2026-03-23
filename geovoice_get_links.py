import asyncio
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        # headless=False allows you to watch the process in real-time
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # Main category URLs to scan
        categories = [
            "https://geovoice.ge/audio/",
            "https://geovoice.ge/dj-studia/",
            "https://geovoice.ge/video-aparatura/",
            "https://geovoice.ge/sasce-ganat-aparatura/",
            "https://geovoice.ge/komutacia-kabel-adampt-konector/",
            "https://geovoice.ge/sadgamebi-sakidebi-aksesuarebi/"
        ]
        
        all_final_pages = []

        for cat_url in categories:
            print(f"📂 Processing category: {cat_url}")
            try:
                # Navigate to the main category page
                await page.goto(cat_url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"⚠️ Could not access URL {cat_url}: {e}")
                continue
            
            page_num = 1
            while True:
                # Store the current page URL
                current_url = page.url
                if current_url not in all_final_pages:
                    all_final_pages.append(current_url)
                    print(f"   ✅ Added: {current_url}")

                # Locate the "Next" pagination button
                next_button = await page.query_selector('.ty-pagination__next')
                
                if next_button:
                    try:
                        print(f"   ➡️ Navigating to page {page_num + 1}...")
                        await next_button.click()
                        
                        # Wait for the DOM to load instead of waiting for full network idle
                        await page.wait_for_load_state("domcontentloaded", timeout=30000)
                        await asyncio.sleep(2) # Short pause for stability
                        page_num += 1
                    except Exception as e:
                        print(f"   ⚠️ Navigation failed: {e}")
                        break
                else:
                    print("   🏁 Reached the end of this category.")
                    break

        # Save all collected links to a text file
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            
            print(f"\n🚀 Done! Collected a total of {len(all_final_pages)} pages.")
            print(f"📂 File saved: all_pages_to_scrape.txt")
        else:
            print("\n❌ No data was collected.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())