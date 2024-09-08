#!/usr/bin/env python3
#
# Analyzes token holders and their common holdings, and generates a pie chart
#
# Example usage:
# $ ./get-common-holding.py HEX 0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39
#
# Outputs:
# 1. HEX-holders.txt (if not already present)
# 2. HEX-common-holdings.txt with descending order of common token holdings
# 3. A pie chart of common holdings in the 'charts' directory
#
# Dependencies:
# - pip install requests tqdm beautifulsoup4 matplotlib numpy
# - get-token-holders.py script in the same directory
#

import sys
import os
import subprocess
import csv
import requests
import time
from tqdm import tqdm
from collections import defaultdict, Counter
import logging
import warnings
import matplotlib.pyplot as plt
import numpy as np
import shutil

# Suppress matplotlib font warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

SCAN_API = "https://api.scan.pulsechain.com/api/v2"
TEMP_DIR = "temp"
IGNORE_FILE = "ignore-tokens.txt"

def run_get_token_holders(token_name, contract_address):
    output_file = f"{token_name}-holders.txt"
    if os.path.exists(output_file):
        return output_file

    # Find the appropriate Python executable
    python_executables = ['python', 'python3', 'py']
    python_exe = None

    # Check the PATH
    logger.info("Checking system PATH:")
    path = os.environ.get('PATH', '')
    for directory in path.split(os.pathsep):
        logger.info(f"  {directory}")

    for exe in python_executables:
        try:
            result = subprocess.run([exe, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                python_exe = exe
                logger.info(f"Found Python: {exe} - {result.stdout.strip()}")
                break
        except FileNotFoundError:
            logger.info(f"Executable not found: {exe}")

    if not python_exe:
        logger.error("No Python executable found. Please ensure Python is installed and in your PATH.")
        logger.error("You may need to restart your command prompt or system after installation.")
        sys.exit(1)

    try:
        result = subprocess.run([python_exe, "get-token-holders.py", token_name, contract_address],
                                capture_output=True, text=True, check=True)
        logger.info(result.stdout)
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running get-token-holders.py: {e}")
        logger.error(f"Command output: {e.output}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("get-token-holders.py not found in the current directory.")
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"Directory contents: {os.listdir('.')}")
        sys.exit(1)

def get_wallet_holdings(address):
    url = f"{SCAN_API}/addresses/{address}/tokens"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error fetching holdings for {address}: {response.status_code}")
        return []

    data = response.json()
    return [(item['token']['symbol'], item['token']['address']) for item in data.get('items', [])]

def load_ignore_tokens():
    if os.path.exists(IGNORE_FILE):
        with open(IGNORE_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip().lower() for line in f)
    return set()

def analyze_common_holdings(token_name, holders_file):
    os.makedirs(TEMP_DIR, exist_ok=True)
    common_holdings = defaultdict(lambda: {'count': 0, 'address': ''})
    ignore_tokens = load_ignore_tokens()

    with open(holders_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        holders = list(csv_reader)

    logger.info(f"Analyzing holdings for {len(holders)} wallets...\n")
    for address, _ in tqdm(holders, desc="Processing wallets"):
        cache_file = os.path.join(TEMP_DIR, f"{address}.txt")

        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                holdings = []
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        holdings.append((parts[0], parts[1]))
        else:
            holdings = get_wallet_holdings(address)
            with open(cache_file, 'w', encoding='utf-8') as f:
                for symbol, token_address in holdings:
                    if symbol is not None and token_address is not None:
                        try:
                            f.write(f"{symbol},{token_address}\n")
                        except UnicodeEncodeError:
                            logger.warning(f"Could not write symbol {symbol} for address {address}. Skipping.")

        for symbol, token_address in holdings:
            if symbol is not None and token_address is not None:
                if symbol.lower() != token_name.lower() and symbol.lower() not in ignore_tokens:
                    common_holdings[symbol]['count'] += 1
                    common_holdings[symbol]['address'] = token_address

        time.sleep(0.1)  # Be nice to the API

    return common_holdings

def write_common_holdings(token_name, common_holdings):
    output_file = f"{token_name}-common-holdings.txt"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        for token, data in sorted(common_holdings.items(), key=lambda x: x[1]['count'], reverse=True):
            csv_writer.writerow([token, data['address'], data['count']])

    logger.info(f"Common holdings written to {output_file}")

def generate_pie_chart(common_holdings, token_name):
    data_counter = Counter({token: data['count'] for token, data in common_holdings.items()})

    sorted_data = data_counter.most_common()
    top_n = 50
    if len(sorted_data) > top_n:
        labels, values = zip(*sorted_data[:top_n])
        other_count = sum(count for _, count in sorted_data[top_n:])
        labels += ('Other',)
        values += (other_count,)
    else:
        labels, values = zip(*sorted_data)

    total = sum(values)
    percentages = [value / total * 100 for value in values]

    plt.figure(figsize=(20, 15))
    wedges, texts, autotexts = plt.pie(percentages, labels=labels, autopct='%1.1f%%', startangle=140, textprops=dict(color="w"))

    plt.setp(texts, size=8, weight="bold")
    plt.setp(autotexts, size=8, weight="bold")

    for i, (label, percentage) in enumerate(zip(labels, percentages)):
        if percentage < 2:
            ang = (wedges[i].theta2 - wedges[i].theta1) / 2. + wedges[i].theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            plt.annotate(f"{label} ({percentage:.1f}%)", xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                         horizontalalignment=horizontalalignment, arrowprops=dict(arrowstyle="-", connectionstyle=connectionstyle))

    plt.title(f'Distribution of Common Holdings for {token_name}')
    plt.axis('equal')

    if len(sorted_data) > top_n:
        other_percentage = (other_count / total) * 100
        note = f"Total percentage held by others outside top {top_n}: {other_percentage:.2f}%"
        plt.figtext(0.5, 0.01, note, wrap=True, horizontalalignment='center', fontsize=10)

    if not os.path.exists('charts'):
        os.makedirs('charts')

    plt.savefig(f'charts/{token_name}_common_holdings.png', bbox_inches='tight')
    plt.close()

    logger.info(f"Pie chart saved to charts/{token_name}_common_holdings.png")

def main():
    if len(sys.argv) != 3:
        logger.error(f"Usage: {sys.argv[0]} <token_name> <contract_address>")
        sys.exit(1)

    token_name = sys.argv[1]
    contract_address = sys.argv[2]

    holders_file = run_get_token_holders(token_name, contract_address)
    common_holdings = analyze_common_holdings(token_name, holders_file)
    write_common_holdings(token_name, common_holdings)
    generate_pie_chart(common_holdings, token_name)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProgram terminated by user.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
