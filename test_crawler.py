import asyncio
import re
from playwright.async_api import async_playwright

async def test_bose_link(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        print(f"🚀 ვამოწმებ Bose-ს ლინკს: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            # 1. NAME
            name_el = await page.query_selector("h1")
            name = await name_el.inner_text() if name_el else "N/A"

            # 2. PRICE (.ty-price-num არის ჩვენი "ოქროს" სელექტორი)
            price_el = await page.query_selector(".ty-price-num")
            if price_el:
                price_text = await price_el.inner_text()
                price = re.sub(r'\D', '', price_text.split('.')[0])
            else:
                price = "0"

            # 3. UNIQUE_ID (.ty-control-group__item - აქ უნდა ამოვიდეს 3505 ან მსგავსი)
            id_el = await page.query_selector(".ty-control-group__item")
            unique_id = await id_el.inner_text() if id_el else "N/A"

            # 4. STATUS
            content = await page.content()
            status = "In Stock" if "მარაგშია" in content or "In Stock" in content else "Out of Stock"

            print("\n🎯 Bose-ს ტესტის შედეგი:")
            print("-" * 30)
            print(f"🆔 UNIQUE_ID: {unique_id.strip()}")
            print(f"📦 NAME: {name.strip()}")
            print(f"💰 PRICE: {price}")
            print(f"✅ STATUS: {status}")
            print("-" * 30)

        except Exception as e:
            print(f"❌ შეცდომა: {e}")
        
        await browser.close()

# ახალი ლინკი
bose_url = "https://geovoice.ge/bose-quietcomfort-ultra-headphones-gen2-desert-gold/"
asyncio.run(test_bose_link(bose_url))