#!/usr/bin/env python3
#
# Produces a text file with the token holders of a given token contract name and address
#
# Script arguments: <name> <token_address>
#
# Example usage
# $ ./get-token-holders.py HEX 0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39
#
# Outputs to HEX-holders.txt with descending order of holders in CSV format: address,amount
#
# Dependencies
# - pip install requests tqdm beautifulsoup4 matplotlib numpy
# - optional: get-html.py in the helpers directory for total holders count and progress bar
#

import sys
import os
import requests
import time
import logging
from tqdm import tqdm
from bs4 import BeautifulSoup
import csv
import numpy as np
from requests.exceptions import RequestException, Timeout, ConnectionError
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

import matplotlib.pyplot as plt

# Import helper functions
from helpers.run import find_python_executable, run_python_script

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

SCAN_API = "https://api.scan.pulsechain.com/api/v2"
SCAN_IPFS = "https://scan.mypinata.cloud/ipfs/bafybeih3olry3is4e4lzm7rus5l3h6zrphcal5a7ayfkhzm5oivjro2cp4/#/token/"

MAX_RETRIES = 5
RETRY_DELAY = 5

def run_get_html(token_address):
    get_html_script = os.path.join('helpers', 'get-html.py')
    if not os.path.exists(get_html_script):
        logger.error(f"{get_html_script} not found in the helpers directory.")
        return False

    url = f"{SCAN_IPFS}{token_address}"

    python_exe = find_python_executable()
    if not python_exe:
        return False

    return run_python_script(get_html_script, url)

def get_total_holders(html_file):
    if not os.path.exists(html_file):
        logger.error(f"{html_file} does not exist.")
        return None

    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    holders_element = soup.find('p', class_='chakra-text', string='Holders')
    if holders_element:
        holders_number = holders_element.find_next('a', class_='chakra-link')
        if holders_number:
            return int(holders_number.text.strip().replace(',', ''))

    logger.error(f"Unable to find holders number in {html_file}.")
    return None

def fetch_token_holders(token_name, token_address, output_file):
    if not run_get_html(token_address):
        logger.error("Failed to retrieve HTML. Exiting.")
        return

    base_url = f"{SCAN_API}/tokens/{token_address}/holders"
    params = {}

    total_holders = get_total_holders('output.html')
    if total_holders is None:
        logger.warning("Unable to determine total number of holders. Progress bar may be inaccurate.")
        total_holders = float('inf')
    else:
        logger.info(f"Holders: {total_holders}\n")

    with open(output_file, 'w', newline='') as f:
        csv_writer = csv.writer(f)

        start_time = time.time()
        holders_processed = 0

        pbar = tqdm(total=total_holders, unit='holders', desc=f"Gathering data")

        all_holders = []
        decimals = None

        try:
            while True:
                for attempt in range(MAX_RETRIES):
                    try:
                        response = requests.get(base_url, params=params, timeout=30)
                        response.raise_for_status()
                        break
                    except (RequestException, Timeout, ConnectionError) as e:
                        if attempt < MAX_RETRIES - 1:
                            logger.warning(f"Error occurred: {e}. Retrying in {RETRY_DELAY} seconds...")
                            time.sleep(RETRY_DELAY)
                        else:
                            logger.error(f"Failed to fetch data after {MAX_RETRIES} attempts. Last error: {e}")
                            return

                data = response.json()
                items = data.get('items', [])

                if not items:
                    break

                for item in items:
                    address = item['address']['hash']
                    value = int(item['value'])

                    if decimals is None:
                        token_info = item.get('token', {})
                        decimals = token_info.get('decimals')
                        if decimals is not None:
                            decimals = int(decimals)
                        else:
                            logger.warning("Unable to determine token decimals. Using raw values.")

                    adjusted_value = value // (10 ** decimals) if decimals is not None else value

                    csv_writer.writerow([address, adjusted_value])
                    all_holders.append((address, adjusted_value))
                    holders_processed += 1
                    pbar.update(1)

                next_page_params = data.get('next_page_params')
                if not next_page_params:
                    break

                params = next_page_params
                time.sleep(1)  # Be nice to the API

        except KeyboardInterrupt:
            logger.info("\nProgram terminated by user.")
        finally:
            pbar.close()

    elapsed_time = time.time() - start_time
    logger.info("\nDone!\n")
    logger.info(f"Total time: {elapsed_time:.2f} seconds")
    logger.info(f"Results written to {output_file}")

    charts_dir = "charts"
    os.makedirs(charts_dir, exist_ok=True)

    create_bar_chart(token_name, all_holders, charts_dir)

def create_bar_chart(token_name, all_holders, charts_dir):
    sorted_holders = sorted(all_holders, key=lambda x: x[1], reverse=True)

    top_n = 50
    top_holders = sorted_holders[:top_n]
    other_holders = sorted_holders[top_n:]

    addresses = [holder[0] for holder in top_holders]
    amounts = np.array([holder[1] for holder in top_holders])

    other_amount = sum(holder[1] for holder in other_holders)

    scale_factor = 1
    while np.max(amounts) > 1e15 or other_amount > 1e15:
        amounts = amounts / 10
        other_amount = other_amount / 10
        scale_factor *= 10

    def format_amount(value):
        return f"{int(value):,}"

    plt.figure(figsize=(14, 9))
    plt.bar(range(len(addresses)), amounts)
    plt.xlabel('Address')
    plt.ylabel(f'Amount (scaled down by {scale_factor:,}x)' if scale_factor > 1 else 'Amount')
    plt.title(f'Top {top_n} Holders of {token_name}')
    plt.xticks(range(len(addresses)), addresses, rotation=90)

    ax = plt.gca()
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format_amount(x * scale_factor)))

    note = f"Total amount held by others outside top {top_n}: {format_amount(other_amount * scale_factor)}"
    plt.figtext(0.5, 0.01, note, wrap=True, horizontalalignment='center', fontsize=10)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    chart_file = os.path.join(charts_dir, f"{token_name}_top_{top_n}_holders.png")
    plt.savefig(chart_file)
    plt.close()
    logger.info(f"Chart saved to {chart_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.error(f"Usage: {sys.argv[0]} <token_name> <token_address>")
        sys.exit(1)

    token_name = sys.argv[1]
    token_address = sys.argv[2]
    output_file = f"{token_name}-holders.txt"

    logger.info(f"Fetching token holders for {token_name}...")

    try:
        fetch_token_holders(token_name, token_address, output_file)
    except KeyboardInterrupt:
        logger.info("\nProgram terminated by user.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
