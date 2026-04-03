import asyncio
from playwright.async_api import async_playwright
import csv
import os

INPUT_FILE: str = "music-store-product-links.txt"
OUTPUT_CSV: str = "music_store_inventory.csv"

def extract_unique_id(url: str) -> str:
    """Extracts the ID from the end of the URL after '--'."""
    if '--' in url:
        return url.split('--')[-1]
    return "N/A"

async def scrape_product_details() -> None:
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] File not found: {INPUT_FILE}")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"[START] Processing {len(urls)} products...")

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-16") as csvfile:
            fieldnames = ['UNIQUE_ID', 'NAME', 'PRICE', 'STATUS', 'LINK']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()

            for index, url in enumerate(urls, 1):
                product_id = extract_unique_id(url)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(0.5)

                    # 1. Name
                    name = ""
                    if await page.locator(".prod_id").count() > 0:
                        name = await page.locator(".prod_id").inner_text()

                    # 2. Price
                    price = ""
                    if await page.locator(".prod_price span").count() > 0:
                        price_text = await page.locator(".prod_price span").inner_text()
                        price = price_text.strip()

                    # 3. Status logic
                    # If price is empty or N/A - Out of Stock.
                    # If price exists, check for "მარაგშია" text.
                    status_display = "Out of Stock"
                    if price and price != "N/A":
                        if await page.locator(".prod-status p").count() > 0:
                            raw_status = await page.locator(".prod-status p").inner_text()
                            if "მარაგშია" in raw_status:
                                status_display = "In Stock"
                    else:
                        price = ""
                        status_display = "Out of Stock"

                    # Write data
                    writer.writerow({
                        'UNIQUE_ID': product_id,
                        'NAME': name.strip() if name else "Unknown",
                        'PRICE': price,
                        'STATUS': status_display,
                        'LINK': url
                    })
                    print(f"[{index}/{len(urls)}] ✅ {product_id} | Price: {price if price else 'Empty'} | Status: {status_display}")

                except Exception as e:
                    print(f"[{index}/{len(urls)}] ❌ Error on {url}: {e}")
                    continue

        await browser.close()
        print(f"\n🎉 Done! Data is saved and cleaned in {OUTPUT_CSV}.")

def main() -> None:
    asyncio.run(scrape_product_details())

if __name__ == "__main__":
    main()