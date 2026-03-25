import asyncio
from playwright.async_api import async_playwright

async def get_geovoice_all_pages():
    async with async_playwright() as p:
        # ვხსნით ბრაუზერს ფონზე
        browser = await p.chromium.launch(headless=True)
        # ვქმნით კონტექსტს რეალური ბრაუზერის მონაცემებით
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # ვიყენებთ Playwright-ის API მოთხოვნას (ეს არის Requests-ის ანალოგი, ოღონდ ბრაუზერის სახელით)
        api_request = context.request

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

        for base_url in categories:
            print(f"\n🚀 Checking Category: {base_url}", flush=True)
            p_num = 1
            
            while True:
                target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
                
                try:
                    # ვაგზავნით "მსუბუქ" მოთხოვნას (HEAD)
                    # ეს არ ტვირთავს გვერდს, მხოლოდ სტატუსს ამოწმებს
                    response = await api_request.get(target_url)
                    
                    # თუ სტატუსი არის 404, ე.ი. გვერდები მორჩა
                    if response.status == 404:
                        print(f"   🛑 Page {p_num}: 404 Found. Category finished.", flush=True)
                        break
                    
                    # თუ სტატუსი არის 200, ე.ი. გვერდი მუშაობს!
                    if response.status == 200:
                        all_final_pages.append(target_url)
                        print(f"   ✅ Page {p_num}: OK", flush=True)
                    else:
                        print(f"   ⚠️ Page {p_num}: Status {response.status}. Stopping.", flush=True)
                        break
                    
                    p_num += 1
                    # მცირე პაუზა, რომ სერვერი არ "გავაგიჟოთ"
                    await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"   ❌ Error: {e}", flush=True)
                    break

        # შენახვა
        if all_final_pages:
            with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
                for url in all_final_pages:
                    f.write(f"{url}\n")
            print(f"\n📊 Total collected: {len(all_final_pages)} pages", flush=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_geovoice_all_pages())