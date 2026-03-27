import asyncio
import logging

class BaseScraper:
    def __init__(self, selectors, logger=None):
        self.selectors = selectors
        self.logger = logger or logging.getLogger(__name__)

    async def run(self, urls, process_page_func):
        from playwright.async_api import async_playwright
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            for url in urls:
                try:
                    data = await process_page_func(page, url)
                    results.append(data)
                except Exception as e:
                    self.logger.error(f"Error processing {url}: {e}")
            await context.close()
            await browser.close()
        return results
