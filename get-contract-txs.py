#!/usr/bin/env python3
#
# Produces a CSV file with the transactions of a given contract address and pie charts for various fields
#
# Example usage
# $ ./get-contract-txs.py HEX <contract address>
#
# Dependencies
# - sudo apt-get install libatk1.0-0 libatk-bridge2.0-0 libcups2 libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2
# - pip install playwright tqdm matplotlib beautifulsoup4 numpy
# - playwright install chromium
#
# Notes
# - For contracts with hundreds of thousands of calls, results may be limited and stop fetching after 400-500k TXs
#

import sys
import csv
import time
import os
import random
from collections import Counter
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np

def extract_txs_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.select('div.grid.grid-cols-12.items-baseline.gap-x-1.border-t.border-gray-200.text-sm')

    txs = []
    for row in rows:
        txn_hash = row.select_one('span.col-span-2 a')['href'].split('/')[-1] if row.select_one('span.col-span-2 a') else ''

        method_elem = row.select_one('div[class*="bg-"]')
        if method_elem:
            method = method_elem.text.strip()
        else:
            method = ''

        block = row.select_one('span a.font-blocknum').text.strip().replace(',', '') if row.select_one('span a.font-blocknum') else ''
        from_addr = row.select_one('span.col-span-2 div.truncate a.text-link-blue')['href'].split('/')[-1] if row.select_one('span.col-span-2 div.truncate a.text-link-blue') else ''

        # New "To" address extraction using reverse parsing
        to_addr = ''
        all_elements = row.find_all(['span', 'div'])
        for i in range(len(all_elements) - 1, -1, -1):
            element = all_elements[i]
            if element.has_attr('class') and 'col-span-2' in element['class']:
                potential_to = element.get_text(strip=True)
                if potential_to.startswith('0x') and len(potential_to) == 42 and potential_to != from_addr:
                    to_addr = potential_to
                    break
                to_link = element.find('a', class_='text-link-blue')
                if to_link and to_link['href'].split('/')[-1] != from_addr:
                    to_addr = to_link['href'].split('/')[-1]
                    break

        value_elem = row.select_one('span.col-span-2 span.text-sm')
        if value_elem:
            value = value_elem.text.strip().split()[0].replace(',', '').replace('"', '')
        else:
            value = ''

        tx = {
            'Txn Hash': txn_hash,
            'Method': method,
            'Block': block,
            'From': from_addr,
            'To': to_addr,
            'Value': value
        }
        txs.append(tx)
    return txs

def generate_pie_chart(data_counter, field_name, coin_name):
    # Sort counter by values and handle the "Other" category if necessary
    sorted_data = data_counter.most_common()
    if len(sorted_data) > 10:
        labels, values = zip(*sorted_data[:10])
        other_count = sum(count for _, count in sorted_data[10:])
        labels += ('Other',)
        values += (other_count,)
    else:
        labels, values = zip(*sorted_data)

    plt.figure(figsize=(14, 10))
    wedges, texts, autotexts = plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, textprops=dict(color="w"))

    plt.setp(texts, size=10, weight="bold")  # Adjust the label font size
    plt.setp(autotexts, size=10, weight="bold")  # Adjust the percentage font size

    # Draw the arrows for small and crowded sections
    for i, (label, value) in enumerate(zip(labels, values)):
        if value / sum(values) < 0.05:  # Arbitrary threshold for "small" slices
            ang = (wedges[i].theta2 - wedges[i].theta1) / 2. + wedges[i].theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            plt.annotate(label, xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                         horizontalalignment=horizontalalignment, arrowprops=dict(arrowstyle="-", connectionstyle=connectionstyle))

    plt.title(f'Distribution of {field_name} for {coin_name}')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Ensure the charts/ directory exists
    if not os.path.exists('charts'):
        os.makedirs('charts')

    plt.savefig(f'charts/{coin_name}_{field_name}.png')
    plt.close()

def fetch_all_txs(url, output_file, coin_name):
    total_txs = 0
    method_counter = Counter()
    from_counter = Counter()
    to_counter = Counter()
    value_counter = Counter()
    fields = ['Txn Hash', 'Method', 'Block', 'From', 'To', 'Value']

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)

            pbar = tqdm(desc="Gathering data", unit="pages", initial=0)
            retry_count = 0
            max_retries = 5
            while True:
                try:
                    page.wait_for_selector('.grid.grid-cols-12', state='visible', timeout=60000)
                    page.wait_for_load_state('networkidle')

                    html_content = page.content()
                    txs = extract_txs_from_html(html_content)
                    total_txs += len(txs)

                    for tx in txs:
                        writer.writerow(tx)
                        method_counter[tx['Method']] += 1
                        from_counter[tx['From']] += 1
                        to_counter[tx['To']] += 1
                        value_counter[tx['Value']] += 1

                    pbar.update(1)
                    pbar.set_postfix({"Total Txs": f"{total_txs:,}"})  # Format with commas for readability

                    next_button = page.query_selector('a[data-test="nav-next"]:not(.text-gray-400)')
                    if next_button:
                        next_button.click()
                        time.sleep(random.uniform(2, 5))  # Random delay between 2 and 5 seconds
                    else:
                        print("\nReached the end of available transactions.")
                        break

                    # Reset retry count on successful iteration
                    retry_count = 0

                    # Restart browser every 1000 pages
                    if pbar.n % 1000 == 0:
                        browser.close()
                        browser = p.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto(url)

                except Exception as e:
                    print(f"\nError encountered: {str(e)}")
                    retry_count += 1
                    if retry_count > max_retries:
                        print("Max retries exceeded. Exiting.")
                        break
                    print(f"Retrying in {2 ** retry_count} seconds...")
                    time.sleep(2 ** retry_count)

            pbar.close()
        browser.close()

    # Generate the pie charts
    generate_pie_chart(method_counter, 'Method', coin_name)
    generate_pie_chart(from_counter, 'From', coin_name)
    generate_pie_chart(to_counter, 'To', coin_name)

    return total_txs

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <name> <address>")
        sys.exit(1)

    name = sys.argv[1]
    address = sys.argv[2]
    url = f"https://otter.pulsechain.com/address/{address}"
    output_file = f"{name}-txs.txt"

    print(f"Fetching transactions for {name}...\n")
    total_txs = fetch_all_txs(url, output_file, name)
    print(f"\nTotal transactions fetched and saved to {output_file}: {total_txs:,}")
    print("Pie charts saved in the 'charts/' directory")
