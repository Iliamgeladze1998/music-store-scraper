import requests
import time

def get_geovoice_all_pages():
    categories = [
        "https://geovoice.ge/audio/",
        "https://geovoice.ge/dj-studia/",
        "https://geovoice.ge/video-aparatura/",
        "https://geovoice.ge/sasce-ganat-aparatura/",
        "https://geovoice.ge/komutacia-kabel-adampt-konector/",
        "https://geovoice.ge/sadgamebi-sakidebi-aksesuarebi/",
        "https://geovoice.ge/sadgamebi-sakidebi/" 
    ]
    
    # რეალური ბრაუზერის "ნიღაბი", რომ სერვერმა არ დაგვბლოკოს
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    all_final_pages = []

    for base_url in categories:
        print(f"\n🚀 Scanning Category: {base_url}", flush=True)
        
        p_num = 1
        while True:
            target_url = f"{base_url}page-{p_num}/" if p_num > 1 else base_url
            
            try:
                # ვაგზავნით მოთხოვნას
                response = requests.get(target_url, headers=headers, timeout=20)
                
                # 🛑 მთავარი მუხრუჭი: თუ სტატუსი არ არის 200 (მაგ. 404), ვჩერდებით
                if response.status_code != 200:
                    print(f"   🛑 Page {p_num} returned {response.status_code}. End of category.", flush=True)
                    break
                
                # დამატებითი დაზღვევა: ვამოწმებთ ხომ არ დაგვაბრუნა პირველ გვერდზე (Redirect)
                if p_num > 1 and response.url.rstrip('/') == base_url.rstrip('/'):
                    print(f"   🔄 Redirect detected. Finishing category.", flush=True)
                    break

                all_final_pages.append(target_url)
                print(f"   ✅ Success: Page {p_num}", flush=True)
                
                p_num += 1
                time.sleep(0.5) # მცირე პაუზა სერვერისთვის

            except Exception as e:
                print(f"   ❌ Network error: {e}", flush=True)
                break

    # შენახვა
    if all_final_pages:
        with open('all_pages_to_scrape.txt', 'w', encoding='utf-8') as f:
            for url in all_final_pages:
                f.write(f"{url}\n")
        print(f"\n📊 Total pages collected: {len(all_final_pages)}", flush=True)

if __name__ == "__main__":
    get_geovoice_all_pages()