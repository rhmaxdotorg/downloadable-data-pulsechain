#!/usr/bin/env python3
#
# Output the full HTML content of a Single Page Application (SPA) given a URL
#
# Example usage
# $ ./get-page-text.py URL
#
# Dependencies
# - sudo apt-get install libatk1.0-0 libatk-bridge2.0-0 libcups2 libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2
# - pip install playwright
# - playwright install chromium
#

import sys
from playwright.sync_api import sync_playwright
import time

def extract_html_from_spa(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        # Wait for the page to load (adjust the time if needed)
        time.sleep(5)

        # Extract the full HTML content
        html_content = page.content()

        browser.close()
        return html_content

def save_html_to_file(html_content, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <url>")
        sys.exit(1)

    url = sys.argv[1]
    html = extract_html_from_spa(url)

    output_file = 'output.html'
    save_html_to_file(html, output_file)
    print(f"HTML content has been saved to {output_file}")
