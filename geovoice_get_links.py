import asyncio
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        # headless=False რომ დაინახო როგორ მუშაობს
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # ძირითადი კატეგორიები
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
            print(f"📂 ვამუშავებ კატეგორიას: {cat_url}")
            try:
                # გადავდივართ კატეგორიის მთავარ გვერდზე
                await page.goto(cat_url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"⚠️ ვერ შევედი ლინკზე {cat_url}: {e}")
                continue
            
            page_num = 1
            while True:
                # მიმდინარე გვერდის შენახვა
                current_url = page.url
                if current_url not in all_final_pages:
                    all_final_pages.append(current_url)
                    print(f"   ✅ დამატებულია: {current_url}")

                # ვეძებთ "Next" ღილაკს
                next_button = await page.query_selector('.ty-pagination__next')
                
                if next_button:
                    try:
                        print(f"   ➡️ გადავდივარ მე-{page_num + 1} გვერდზე...")
                        await next_button.click()
                        
                        # 🎯 აქ არის მთავარი ცვლილება: აღარ ველოდებით networkidle-ს
                        await page.wait_for_load_state("domcontentloaded", timeout=30000)
                        await asyncio.sleep(2) # მცირე პაუზა სტაბილურობისთვის
                        page_num += 1
                    except Exception as e:
                        print(f"   ⚠️ გვერდზე გადასვლა ვერ მოხერხდა: {e}")
                        break
                else:
                    print("   🏁 ამ კატეგორიაში გვერდები დასრულდა.")
                    break

        # ყველა ლინკის შენახვა ფაილში
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            
            print(f"\n🚀 მზად არის! სულ შეგროვდა {len(all_final_pages)} გვერდი.")
            print(f"📂 ფაილი: all_pages_to_scrape.txt")
        else:
            print("\n❌ მონაცემები ვერ შეგროვდა.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())