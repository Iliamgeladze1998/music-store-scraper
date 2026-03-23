import time
from playwright.sync_api import sync_playwright

def get_all_subcategory_links():
    with sync_playwright() as p:
        # headless=False რომ დაინახო რას აკეთებს
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        print("საიტზე შესვლა...")
        page.goto("https://acoustic.ge", wait_until="networkidle")
        
        # ვპოულობთ ყველა მთავარ კატეგორიას
        # ვიყენებთ უფრო ზუსტ სელექტორს, რომ მხოლოდ ზედა მენიუ ავიღოთ
        main_categories = page.query_selector_all(".ty-menu__item-link")
        
        all_links = []
        processed_titles = set()
        
        print(f"ნაპოვნია მენიუს {len(main_categories)} ელემენტი. ვიწყებ ფილტრაციას...")

        for category in main_categories:
            # 1. ვამოწმებთ არის თუ არა ხილვადი
            if not category.is_visible():
                continue
                
            cat_name = category.inner_text().strip()
            
            # 2. ვამოწმებთ სახელს და დუბლიკატს
            if not cat_name or cat_name in processed_titles:
                continue
                
            processed_titles.add(cat_name)
            print(f"ვამუშავებ კატეგორიას: {cat_name}")

            try:
                # მაუსის მიტანა
                category.hover()
                time.sleep(1.5) # ცოტა მეტი დრო მივცეთ მენიუს გამოსაჩენად
                
                # ვიღებთ მხოლოდ იმ ქველინკებს, რომლებიც ამ წამს გამოჩნდა
                sub_links = page.query_selector_all(".ty-menu__submenu-link")
                
                current_cat_links = 0
                for link_el in sub_links:
                    if link_el.is_visible():
                        href = link_el.get_attribute("href")
                        if href and href not in all_links:
                            all_links.append(href)
                            current_cat_links += 1
                
                print(f"  -- დამატებულია {current_cat_links} ქვეკატეგორია")
                
            except Exception as e:
                print(f"  -- შეცდომა {cat_name}-ზე: {e}")

        # ფაილში შენახვა
        with open("subcategory_links.txt", "w", encoding="utf-8") as f:
            for link in all_links:
                f.write(link + "\n")
                
        print(f"\nწარმატება! სულ შეგროვდა {len(all_links)} ლინკი.")
        print("ნახე ფაილი: subcategory_links.txt")
        
        browser.close()

if __name__ == "__main__":
    get_all_subcategory_links()