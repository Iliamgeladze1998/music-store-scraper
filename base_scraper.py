import asyncio
import logging
from playwright.async_api import async_playwright
from config import SCRAPER_CONFIG

class BaseScraper:
    def __init__(self, selectors, max_concurrent=None, logger=None):
        self.selectors = selectors
        self.max_concurrent = max_concurrent or SCRAPER_CONFIG['max_concurrent_tasks']
        self.logger = logger or logging.getLogger(__name__)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.browser = None
        self.context = None

    async def init_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=SCRAPER_CONFIG['headless'])
        self.context = await self.browser.new_context()
        self.logger.info('Browser and context initialized')

    async def close_browser(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        self.logger.info('Browser and context closed')

    async def block_resources(self, route):
        url = route.request.url
        if any(pat in url for pat in SCRAPER_CONFIG['resource_block_patterns']):
            await route.abort()
        else:
            await route.continue_()

    async def fetch_with_retries(self, coro, *args, **kwargs):
        attempts = SCRAPER_CONFIG['retry_attempts']
        backoff = SCRAPER_CONFIG['retry_backoff']
        for i in range(attempts):
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f'Retry {i+1}/{attempts} failed: {e}')
                await asyncio.sleep(backoff * (2 ** i))
        self.logger.error(f'All {attempts} attempts failed for {coro.__name__}')
        return None

    async def run(self, urls, process_func):
        await self.init_browser()
        results = []
        async def worker(url):
            async with self.semaphore:
                try:
                    page = await self.context.new_page()
                    await page.route('**/*', self.block_resources)
                    result = await self.fetch_with_retries(process_func, page, url)
                    if result:
                        results.append(result)
                    await page.close()
                except Exception as e:
                    self.logger.error(f'Worker failed for {url}: {e}')
        tasks = [asyncio.create_task(worker(url)) for url in urls]
        await asyncio.gather(*tasks)
        await self.close_browser()
        return results
