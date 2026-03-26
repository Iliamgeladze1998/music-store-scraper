import asyncio
import time
from playwright.async_api import async_playwright, Route

async def block_unnecessary_resources(route: Route):
    """Block images, fonts, and analytics to speed up page loading."""
    if any(ext in route.request.url for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.woff', '.woff2', '.ttf', 'analytics', 'gtag']):
        await route.abort()
    else:
        await route.continue_()


async def scan_single_category(context, base_url, category_num):
    """
    Scans ONE category with its OWN dedicated page.
    This prevents state/cookie conflicts.
    """
    # Each category gets its own dedicated page
    page = await context.new_page()
    await page.route("**/*", block_unnecessary_resources)
    
    category_pages = []
    p_num = 1
    
    print(f"\nSCANNING CATEGORY {category_num}: {base_url}", flush=True)
    
    try:
        while True:
            target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
            
            try:
                # ქუქიების გასუფთავება ყოველ ნაბიჯზე (original logic)
                await context.clear_cookies()
                
                # გვერდზე გადასვლა
                response = await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                
                print(f"   Page {p_num} Status: {response.status}", flush=True)

                if response.status == 404:
                    print(f"   Page {p_num} is 404. Moving to next category.", flush=True)
                    break

                # დალოდება რენდერინგისთვის (original: 2.5s)
                await asyncio.sleep(2.5)

                # პროდუქტების შემოწმება (original exact logic)
                products = await page.query_selector_all(".product-item, .ty-column4")
                
                if len(products) > 0:
                    if target_url not in category_pages:
                        category_pages.append(target_url)
                    print(f"   Success: Page {p_num} - Found {len(products)} products", flush=True)
                    p_num += 1
                    # პაუზა ბლოკირების თავიდან ასაცილებლად (original: 3s)
                    await asyncio.sleep(3) 
                else:
                    print(f"   Page {p_num} is empty. Category ends.", flush=True)
                    break

            except Exception as e:
                print(f"   Error at {target_url}: {str(e)[:50]}", flush=True)
                break
    
    finally:
        await page.close()
    
    print(f"   Category {category_num} complete: {len(category_pages)} pages found", flush=True)
    return category_pages


async def get_geovoice_all_pages():
    start_time = time.time()
    
    print(f"\n{'#'*70}", flush=True)
    print(f"# GEOVOICE LINK SCANNER - FIXED", flush=True)
    print(f"# Mode: Parallel categories, each with dedicated page", flush=True)
    print(f"# Start: {time.strftime('%H:%M:%S')}", flush=True)
    print(f"{'#'*70}\n", flush=True)
    
    async with async_playwright() as p:
        print("Launching browser...", flush=True)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )
        print("Browser launched\n", flush=True)

        # კონტექსტი ადამიანური პარამეტრებით
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},  # Optimized viewport
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9,ka;q=0.8",
                "Referer": "https://geovoice.ge/"
            }
        )

        categories = [
            "https://geovoice.ge/audio/",
            "https://geovoice.ge/dj-studia/",
            "https://geovoice.ge/video-aparatura/",
            "https://geovoice.ge/sasce-ganat-aparatura/",
            "https://geovoice.ge/komutacia-kabel-adampt-konector/",
            "https://geovoice.ge/sadgamebi-sakidebi-aksesuarebi/",
            "https://geovoice.ge/sadgamebi-sakidebi/" 
        ]

        print(f"Found {len(categories)} categories. Starting extraction...", flush=True)
        for idx, url in enumerate(categories, 1):
            print(f"Visiting category {idx}: {url}", flush=True)

        # Create tasks for each category - each with its own page
        tasks = []
        for cat_num, base_url in enumerate(categories, 1):
            task = scan_single_category(context, base_url, cat_num)
            tasks.append(task)

        # Run all categories in parallel
        print(f"Starting parallel category scans...\n", flush=True)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results from all categories
        all_final_pages = []
        for cat_num, result in enumerate(results, 1):
            if isinstance(result, list):
                all_final_pages.extend(result)
                print(f"Category {cat_num}: {len(result)} pages collected", flush=True)
            elif isinstance(result, Exception):
                print(f"Category {cat_num}: ERROR - {str(result)[:40]}", flush=True)

        await context.close()
        await browser.close()

        # --- Save results and print summary ---
        if all_final_pages:
            # Save to geovoice_subcategory_links.txt for consistency
            with open('geovoice_subcategory_links.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            elapsed = time.time() - start_time
            print(f"\n{'='*70}")
            print(f"GEOVOICE SCAN SUMMARY:")
            print(f"Total Geovoice pages found: {len(all_final_pages)}")
            print(f"Saved to: geovoice_subcategory_links.txt")
            print(f"Time: {elapsed:.1f}s ({elapsed/len(categories):.1f}s per category avg)", flush=True)
            print(f"{'='*70}\n", flush=True)
        else:
            print(f"\nNo pages were found for Geovoice!", flush=True)

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())