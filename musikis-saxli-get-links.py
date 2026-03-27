import asyncio
from playwright.async_api import async_playwright
import os

# Senior-level: constants, type hints, and robust structure
CATEGORIES: list[str] = [
    "https://musikis-saxli.ge/guitar",
    "https://musikis-saxli.ge/bass",
    "https://musikis-saxli.ge/drum",
    "https://musikis-saxli.ge/keyboards-instruments",
    "https://musikis-saxli.ge/music-lover",
    "https://musikis-saxli.ge/studio",
    "https://musikis-saxli.ge/sound-effects",
    "https://musikis-saxli.ge/dj",
    "https://musikis-saxli.ge/orchestral-instruments",
    "https://musikis-saxli.ge/pro-audio",
    "https://musikis-saxli.ge/lighting",
    "https://musikis-saxli.ge/commutation",
    "https://musikis-saxli.ge/others"
]

FILE_NAME: str = "music-store-all-links.txt"

async def load_existing_links() -> set[str]:
    """Load existing links from the file to avoid duplicates."""
    if not os.path.exists(FILE_NAME):
        return set()
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

async def save_links_to_file(links: set[str]) -> None:
    """Save a set of links to the file, overwriting it."""
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        for link in sorted(links):
            f.write(link + "\n")
    print(f"[INFO] Saved {len(links)} unique links to {FILE_NAME}")

async def scrape_music_store() -> None:
    """Main scraping function for all categories, avoiding duplicate links."""
    all_links = await load_existing_links()
    print(f"[INIT] Loaded {len(all_links)} existing links from {FILE_NAME}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for base_url in CATEGORIES:
            page_num = 1
            print(f"[CATEGORY] Processing: {base_url}")

            while True:
                target_url = f"{base_url}?page={page_num}"
                print(f"[PAGE] Checking: {target_url}")

                try:
                    await page.goto(target_url, wait_until="domcontentloaded")
                    await asyncio.sleep(0.5)  # Short sleep for stability

                    # Save the current page URL if not already present
                    if target_url not in all_links:
                        all_links.add(target_url)
                        print(f"[LINK] Added: {target_url}")
                    else:
                        print(f"[LINK] Skipped duplicate: {target_url}")

                    # Check for the presence of the Next Page button
                    next_button = page.locator(".main_pagination li:last-child a")
                    has_next = False
                    if await next_button.count() > 0:
                        href_value = await next_button.get_attribute("href")
                        # If href is '#' or empty, this is the last page
                        if href_value == "#" or not href_value:
                            print(f"[END] Last page reached ({page_num}). Moving to next category.")
                            break
                        has_next = True
                    else:
                        # If there is no pagination, only one page exists
                        print(f"[END] No navigation button. Only one page in this category.")
                        break

                    page_num += 1
                    if not has_next:
                        break

                except Exception as e:
                    print(f"[ERROR] Exception on {target_url}: {e}")
                    break

        await browser.close()
        await save_links_to_file(all_links)
        print(f"[DONE] All links have been updated in: {FILE_NAME}")

def main() -> None:
    asyncio.run(scrape_music_store())

if __name__ == "__main__":
    main()