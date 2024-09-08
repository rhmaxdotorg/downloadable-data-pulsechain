#!/usr/bin/env python3

# Checks Dex Screener API for pairs data of a given token address and generates a pie chart based on 24h volume
#
# Example usage:
# $ ./get-token-volume.py HEX 0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39
#

import sys
import requests
import csv
from typing import List, Dict
from collections import Counter
import matplotlib.pyplot as plt
import os

def get_pairs(token_address: str) -> List[Dict]:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('pairs', [])
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        return []

def write_to_csv(pairs: List[Dict], filename: str):
    if not pairs:
        print("No pairs data to write to CSV.")
        return

    fieldnames = ['dexId', 'pairAddress', 'baseTokenSymbol', 'quoteTokenSymbol', 'volume24h']

    # Sort pairs by dexId in ascending order and filter out pairs with no volume
    sorted_pairs = sorted(
        [pair for pair in pairs if pair.get('volume', {}).get('h24', 0) > 0],
        key=lambda x: x.get('dexId', '')
    )

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # writer.writeheader()
        for pair in sorted_pairs:
            writer.writerow({
                'dexId': pair.get('dexId', ''),
                'pairAddress': pair.get('pairAddress', ''),
                'baseTokenSymbol': pair.get('baseToken', {}).get('symbol', ''),
                'quoteTokenSymbol': pair.get('quoteToken', {}).get('symbol', ''),
                'volume24h': pair.get('volume', {}).get('h24', '')
            })

def calculate_total_volume(pairs: List[Dict]) -> float:
    return sum(pair.get('volume', {}).get('h24', 0) for pair in pairs if pair.get('volume', {}).get('h24', 0) > 0)

def generate_pie_chart(pairs: List[Dict], coin_name: str):
    # Calculate volume for each DEX
    dex_volume = Counter()
    for pair in pairs:
        volume = pair.get('volume', {}).get('h24', 0)
        if volume > 0:
            dex_volume[pair.get('dexId', 'Unknown')] += volume

    # Sort and handle the "Other" category if necessary
    sorted_data = dex_volume.most_common()
    if len(sorted_data) > 10:
        labels, values = zip(*sorted_data[:9])
        other_count = sum(count for _, count in sorted_data[9:])
        labels += ('Other',)
        values += (other_count,)
    else:
        labels, values = zip(*sorted_data)

    # Calculate percentages
    total = sum(values)
    percentages = [(value / total) * 100 for value in values]

    # Create labels with dexId and percentage
    labels_with_percentages = [f'{label}: {percentage:.1f}%' for label, percentage in zip(labels, percentages)]

    plt.figure(figsize=(14, 10))
    wedges, texts = plt.pie(values, labels=labels_with_percentages, startangle=140,
                            labeldistance=1.05, textprops={'fontsize': 9, 'fontweight': 'bold'})

    plt.title(f'Distribution of 24h Volume for {coin_name}')
    plt.axis('equal')

    # Ensure the charts/ directory exists
    if not os.path.exists('charts'):
        os.makedirs('charts')

    plt.savefig(f'charts/{coin_name}_volume.png', bbox_inches='tight')
    plt.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: ./get-token-volume.py <name> <token_address>")
        sys.exit(1)

    name = sys.argv[1]
    token_address = sys.argv[2]

    pairs = get_pairs(token_address)

    if pairs:
        csv_filename = f"{name}-volume.txt"
        write_to_csv(pairs, csv_filename)
        print(f"Volume data has been written to {csv_filename}\n")

        total_volume = calculate_total_volume(pairs)
        print(f"Total 24h volume: ${total_volume:,.2f}\n")

        generate_pie_chart(pairs, name)
        print(f"Pie chart has been saved as charts/{name}_volume.png")
    else:
        print("No pairs found for the given token address.")

if __name__ == "__main__":
    main()
