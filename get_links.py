import time
from playwright.sync_api import sync_playwright

def get_all_subcategory_links():
    with sync_playwright() as p:
        # headless=False so you can see the menu navigation in real-time
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        print("🚀 Navigating to site...")
        page.goto("https://acoustic.ge", wait_until="networkidle")
        
        # Locate all main categories using the menu item selector
        main_categories = page.query_selector_all(".ty-menu__item-link")
        
        all_links = []
        processed_titles = set()
        
        print(f"📦 Found {len(main_categories)} menu items. Starting filtration...")

        for category in main_categories:
            # 1. Check if the category is visible
            if not category.is_visible():
                continue
                
            cat_name = category.inner_text().strip()
            
            # 2. Check name validity and avoid duplicates
            if not cat_name or cat_name in processed_titles:
                continue
                
            processed_titles.add(cat_name)
            print(f"🔄 Processing category: {cat_name}")

            try:
                # Hover over the category to trigger the dropdown menu
                category.hover()
                time.sleep(1.5) # Allow time for the submenu to appear
                
                # Extract sub-links that become visible upon hover
                sub_links = page.query_selector_all(".ty-menu__submenu-link")
                
                current_cat_links = 0
                for link_el in sub_links:
                    if link_el.is_visible():
                        href = link_el.get_attribute("href")
                        if href and href not in all_links:
                            all_links.append(href)
                            current_cat_links += 1
                
                print(f"   -- Added {current_cat_links} subcategories")
                
            except Exception as e:
                print(f"   -- Error processing {cat_name}: {e}")

        # Save all unique links to a text file
        with open("subcategory_links.txt", "w", encoding="utf-8") as f:
            for link in all_links:
                f.write(link + "\n")
                
        print(f"\n✅ Success! Total of {len(all_links)} links collected.")
        print("📂 Check the file: subcategory_links.txt")
        
        browser.close()

if __name__ == "__main__":
    get_all_subcategory_links()