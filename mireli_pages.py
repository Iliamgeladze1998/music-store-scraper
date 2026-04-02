#!/usr/bin/env python3
"""
Script to identify and save all valid pagination links for the "Klavishebiani" category on mireli.ge
"""

import requests
import time
from urllib.parse import urljoin

def discover_pagination_links():
    """
    Discover all valid pagination pages for the Klavishebiani category.
    Stops when a redirect to the main domain is detected.
    """
    base_url = "https://mireli.ge/product-category/klavishebiani/page/"
    per_page_param = "?perpage=64"
    
    valid_urls = []
    page_num = 1
    
    print(f"Starting pagination discovery from: {base_url}{page_num}/{per_page_param}")
    
    while True:
        # Construct the URL for current page
        current_url = f"{base_url}{page_num}/{per_page_param}"
        
        try:
            print(f"Checking page {page_num}...")
            
            # Make request with timeout and allow redirects
            response = requests.get(current_url, timeout=10, allow_redirects=True)
            
            # Special handling for page 1
            if page_num == 1:
                # Allow redirect for page 1 and add the final URL
                if response.status_code == 200 and "/product-category/klavishebiani/" in response.url:
                    valid_urls.append(response.url)
                    print(f"Page 1 redirect accepted: {current_url} -> {response.url}")
                    page_num += 1
                    time.sleep(0.5)
                else:
                    print(f"Page 1 failed with status {response.status_code} or invalid URL. Stopping.")
                    break
            else:
                # For pages 2+, check if redirect happened
                if response.url != current_url:
                    print(f"Redirect detected: Requested {current_url} but got {response.url}. Stopping.")
                    break
                
                # Only add URL if status is 200 AND no redirect happened AND contains category path
                if response.status_code == 200 and response.url == current_url and "/product-category/klavishebiani/" in response.url:
                    valid_urls.append(current_url)
                    print(f"Found valid page: {current_url}")
                    page_num += 1
                    time.sleep(0.5)
                else:
                    print(f"Page {page_num} invalid (status {response.status_code} or missing category path). Stopping.")
                    break
                
        except requests.exceptions.Timeout:
            print(f"Timeout at page {page_num}. Stopping.")
            break
        except requests.exceptions.RequestException as e:
            print(f"Request error at page {page_num}: {e}. Stopping.")
            break
    
    return valid_urls

def save_urls_to_file(urls, filename="mireli_pagination_links.txt"):
    """
    Save the list of URLs to a text file
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        print(f"Saved {len(urls)} valid URLs to {filename}")
    except Exception as e:
        print(f"Error saving URLs to file: {e}")

def main():
    """
    Main function to discover pagination links and save them
    """
    print("=" * 50)
    print("Mireli Pagination Link Discovery")
    print("=" * 50)
    
    # Discover all valid pagination links
    valid_urls = discover_pagination_links()
    
    if valid_urls:
        print(f"\nDiscovery complete! Found {len(valid_urls)} valid pages:")
        for i, url in enumerate(valid_urls, 1):
            print(f"  {i}. {url}")
        
        # Save URLs to file
        save_urls_to_file(valid_urls)
        
        print(f"\n{'=' * 50}")
        print(f"SUCCESS: {len(valid_urls)} pages saved to mireli_pagination_links.txt")
        print(f"{'=' * 50}")
    else:
        print("\nNo valid pages found.")

if __name__ == "__main__":
    main()
