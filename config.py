# Configuration for scraping (selectors, URLs, constants)

ACOUSTIC_SELECTORS = {
    'product_container': '.ty-column4, .ty-compact-list__content',
    'name': 'a.product-title',
    'sku': [
        "[id^='product_code_']",
        ".product-code",
        "[data-sku]",
        ".sku-value"
    ],
    'price': '.ty-price',
    'status_text': ['არ არის', 'Out of Stock'],
}

GEOVOICE_SELECTORS = {
    'product_container': '.product-list-item',
    'name': '.product-title',
    'sku': [
        ".sku-value",
        ".product-code",
        "[data-sku]",
        "span[class*='sku']"
    ],
    'price': '.product-price',
    'status_text': ['არ არის', 'Out of Stock'],
}

SCRAPER_CONFIG = {
    'max_concurrent_tasks': 5,
    'retry_attempts': 3,
    'retry_backoff': 2,  # seconds, exponential
    'headless': True,
    'resource_block_patterns': [
        '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.woff', '.woff2', '.ttf', '.css',
        'analytics', 'gtag', 'tracking', 'doubleclick', 'facebook', 'google-analytics', 'media', 'font', 'adservice'
    ],
}