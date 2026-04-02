#!/usr/bin/env python3
"""
Script to scrape product data from Mireli category pages using pagination links
"""

import requests
import re
import time
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_unique_id(name, url):
    """
    Dynamic UNIQUE_ID extraction - removes brands, finds actual model codes
    """
    if not name:
        return "N/A"
    
    # Common brand names to remove from start
    brand_names = ['KORG', 'YAMAHA', 'CASIO', 'ROLAND', 'GEWA', 'KLAVIA', 'AKAI', 'PEARL', 'MEDELI', 'HAMILTON']
    
    # Clean name by removing brand from start
    clean_name = name.upper()
    for brand in brand_names:
        if clean_name.startswith(brand + ' '):
            clean_name = clean_name[len(brand) + 1:].strip()
        elif clean_name.startswith(brand + '-'):
            clean_name = clean_name[len(brand) + 1:].strip()
    
    # Split into words
    words = clean_name.split()
    
    # Step A: Look for first string with Number AND mostly Uppercase/Alphanumeric
    for word in words:
        word_upper = word.upper()
        # Check if contains number and is mostly alphanumeric
        if re.search(r'\d', word_upper) and len(re.findall(r'[A-Z0-9]', word_upper)) >= len(word_upper) * 0.7:
            # Remove special chars, keep alphanumeric and dashes
            clean_code = re.sub(r'[^A-Z0-9\-]', '', word_upper)
            if len(clean_code) >= 2:  # Minimum length for model code
                return clean_code.strip()
    
    # Step B: Strict fallback - use URL slug
    if url:
        # Extract slug from URL (last part before trailing slash)
        url_parts = url.strip('/').split('/')
        if len(url_parts) > 1:
            slug = url_parts[-1]
            # Clean slug - remove non-alphanumeric except dashes
            clean_slug = re.sub(r'[^A-Z0-9a-z\-]', '', slug)
            if len(clean_slug) >= 2:
                return clean_slug.lower()
    
    # Step C: Emergency fallback - use hash
    return "ID_" + str(abs(hash(name)))[:8]

def ensure_unique_ids(products):
    """
    Ensure all UNIQUE_ID values are unique
    """
    seen_ids = set()
    for product in products:
        unique_id = product['UNIQUE_ID']
        if unique_id in seen_ids:
            # Make unique by adding URL segment or counter
            url_parts = product['LINK'].strip('/').split('/')
            url_part = url_parts[-2] if len(url_parts) > 1 else str(len(seen_ids))
            product['UNIQUE_ID'] = f"{unique_id}_{url_part[:4]}"
        seen_ids.add(product['UNIQUE_ID'])
    return products

def clean_price(price_text):
    """
    Clean price text and convert to integer
    Handles Georgian format: "4 699,00 ₾" -> 4699
    """
    if not price_text:
        return 0
    
    # Remove all spaces and the currency symbol ₾
    clean_str = price_text.replace(' ', '').replace('₾', '')
    
    # Replace the comma , with a dot .
    clean_str = clean_str.replace(',', '.')
    
    # Convert to float first, then immediately to int to remove decimal places
    try:
        final_price = int(float(clean_str))
        return final_price
    except (ValueError, TypeError):
        return 0

def scrape_category_page(url, page_num, total_pages):
    """
    Scrape product data from a single category page
    """
    products = []
    
    try:
        print(f"Scraping Page {page_num}/{total_pages}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all product cards using lambda to match both classes
        product_cards = soup.find_all('div', class_=lambda x: x and 'column-item' in str(x) and 'product' in str(x))
        
        if not product_cards:
            print(f"  No products found on page {page_num}")
            return products
        
        print(f"  Found {len(product_cards)} products")
        
        for card in product_cards:
            try:
                # Extract Full Title and URL
                title_element = card.find('h3', class_='product-title')
                if not title_element:
                    continue
                
                title_link = title_element.find('a')
                if not title_link:
                    continue
                
                full_title = title_link.get_text().strip()
                product_url = title_link.get('href', '')
                
                # Extract Price - Priority: Sale Price (ins) first, then Regular Price (span)
                price = 0
                price_text = ""
                
                # Priority 1: Look for sale price in ins span.woocommerce-Price-amount bdi
                sale_price_tag = card.select_one('ins span.woocommerce-Price-amount bdi')
                if sale_price_tag:
                    price_text = sale_price_tag.get_text()
                else:
                    # Priority 2: Look for regular price in span.woocommerce-Price-amount bdi
                    regular_price_tag = card.select_one('span.woocommerce-Price-amount bdi')
                    if regular_price_tag:
                        price_text = regular_price_tag.get_text()
                
                # Clean the price and convert to integer
                if price_text:
                    price = clean_price(price_text)
                
                # Extract Stock Status
                stock_status = "Out of Stock"
                stock_element = card.find('div', class_='product-stock')
                if stock_element:
                    stock_text = stock_element.get_text().strip()
                    if "მარაგშია" in stock_text:
                        stock_status = "In Stock"
                
                # Extract UNIQUE_ID using robust function
                unique_id = extract_unique_id(full_title, product_url)
                
                products.append({
                    'UNIQUE_ID': unique_id,
                    'NAME': full_title,
                    'PRICE': price,
                    'STATUS': stock_status,
                    'LINK': product_url
                })
                
            except Exception as e:
                print(f"  Error parsing product: {e}")
                continue
        
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching page {url}: {e}")
    except Exception as e:
        print(f"  Error processing page {url}: {e}")
    
    return products

def read_pagination_links(filename="mireli_pagination_links.txt"):
    """
    Read pagination URLs from file
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

def save_to_csv(products, filename="mireli_products.csv"):
    """
    Save products to CSV file
    """
    if not products:
        print("No products to save.")
        return
    
    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ['UNIQUE_ID', 'NAME', 'PRICE', 'STATUS', 'LINK']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for product in products:
                writer.writerow(product)
        
        print(f"Saved {len(products)} products to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    """
    Main function to scrape all category pages
    """
    print("=" * 60)
    print("Mireli Product Scraper")
    print("=" * 60)
    
    # Read pagination links
    urls = read_pagination_links()
    if not urls:
        print("No pagination URLs found. Please run mireli_pages.py first.")
        return
    
    print(f"Found {len(urls)} pages to scrape")
    
    all_products = []
    
    for i, url in enumerate(urls, 1):
        products = scrape_category_page(url, i, len(urls))
        all_products.extend(products)
        
        # Add delay between requests
        if i < len(urls):
            time.sleep(1)
    
    print(f"\n{'=' * 60}")
    print(f"Scraping complete. Total products saved: {len(all_products)}")
    
    # Ensure all UNIQUE_ID values are unique
    all_products = ensure_unique_ids(all_products)
    
    # Save to CSV
    save_to_csv(all_products)
    
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
