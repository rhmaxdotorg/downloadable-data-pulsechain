"""
PulseChain Hearts Law Simulator
==============================
Part of RHMAX's Downloadable Data PulseChain Tools
https://github.com/rhmaxdotorg/downloadable-data-pulsechain

⚠️ THIS SCRIPT IS FOR EDUCATIONAL AND ENTERTAINMENT PURPOSES ONLY ⚠️

A community extension adding Hearts Law price relationship simulation using the
existing infrastructure for PulseChain data analysis.

Dependencies:
- Python (installed via RHMAX's setup scripts)
- Requests library (installed via RHMAX's setup scripts)
- DEX Screener API access (public, no key needed)

Usage:
    python hearts-law-sim.py <token_name> <pair_address>

Example:
    python hearts-law-sim.py hex 0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39

Features:
- Analyzes price relationships in liquidity pairs
- Calculates theoretical future prices based on pair movement
- Tracks potential X calculations
- Saves history to <token>-hearts-law.txt

Richard Heart's explanation of liquidity bonding:
https://x.com/superhexwin/status/1844208597024244011

IMPORTANT DISCLAIMERS:
1. This is NOT financial advice
2. Results are PURELY THEORETICAL and don't account for:
   - Market psychology
   - Trading volume
   - External events
   - Multiple trading pairs
3. Real markets are far more complex
4. Past relationships don't predict future movement
5. DEX Screener data may be incomplete

Community Contribution from Author: 
@CryptoKong145 (cryptokong.pls.fyi)
Version: 1.0
"""



import sys
import requests
from datetime import datetime
import os

def get_pair_info(pair_address, target_token_name):
    """
    Fetch trading pair information from the DEX Screener API.
    """
    url = f"https://api.dexscreener.com/latest/dex/pairs/pulsechain/{pair_address}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'pairs' in data and len(data['pairs']) > 0:
            pair = data['pairs'][0]
            
            # Determine which token in the pair is our target
            quote_is_target = pair['quoteToken']['symbol'].upper() == target_token_name.upper()
            
            return {
                'target_token': pair['quoteToken']['symbol'] if quote_is_target else pair['baseToken']['symbol'],
                'target_name': pair['quoteToken']['name'] if quote_is_target else pair['baseToken']['name'],
                'paired_token': pair['baseToken']['symbol'] if quote_is_target else pair['quoteToken']['symbol'],
                'paired_name': pair['baseToken']['name'] if quote_is_target else pair['quoteToken']['name'],
                'price_native': float(pair['priceNative']),
                'price_usd': float(pair['priceUsd']) if 'priceUsd' in pair else None
            }
    return None

def calculate_x(current_price, future_price):
    """
    Calculate the number of Xs between two prices.
    """
    if current_price > 0:
        return future_price / current_price
    return 0

def read_existing_content(filename):
    """
    Read existing content from file if it exists.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def hearts_law_sim(target_token_name, pair_addresses):
    """
    Perform Hearts Law simulation for multiple pairs of a given token.
    """
    results = []
    first_pair_info = None
    
    for pair_address in pair_addresses:
        pair_info = get_pair_info(pair_address, target_token_name)
        
        if not pair_info:
            print(f"Error: Could not fetch information for pair address {pair_address}")
            continue
            
        if not first_pair_info:
            first_pair_info = pair_info
            
        print(f"\nPair Analysis for {pair_address}:")
        print(f"Analyzing token: {pair_info['target_token']} ({pair_info['target_name']})")
        print(f"Paired with: {pair_info['paired_token']} ({pair_info['paired_name']})")
        print(f"Current Price in {pair_info['paired_token']}: {pair_info['price_native']}")
        if pair_info['price_usd']:
            print(f"Current USD Price: ${pair_info['price_usd']:.10f}")
        
        # Get experimental price for the paired token
        experimental_paired_price = float(input(f"\nWhat is your experimental {pair_info['paired_token']} price in USD? "))
        
        # Calculate new price based on Hearts Law
        new_hearts_law_price_usd = pair_info['price_native'] * experimental_paired_price
        
        # Calculate Xs
        current_price_usd = pair_info['price_usd'] if pair_info['price_usd'] else 0
        potential_x = calculate_x(current_price_usd, new_hearts_law_price_usd)

        results.append({
            'pair_address': pair_address,
            'pair_info': pair_info,
            'experimental_paired_price': experimental_paired_price,
            'new_hearts_law_price': new_hearts_law_price_usd,
            'potential_x': potential_x
        })

        # Print immediate results
        print(f"\nCalculated Results:")
        print(f"Hearts Law Calculated Price: ${new_hearts_law_price_usd:.10f}")
        print(f"Potential X: {potential_x:.2f}x")

    if not results or not first_pair_info:
        print("No valid pairs found.")
        return

    # Create filename using the actual token symbol from the first pair
    filename = f"{first_pair_info['target_token']}-hearts-law.txt"
    
    try:
        # Read existing content
        existing_content = read_existing_content(filename)
        
        # Open file for writing new content
        with open(filename, 'w', encoding='utf-8') as f:
            # Write new analysis at the top
            f.write(f"Hearts Law Analysis for {first_pair_info['target_token']}\n")
            f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")

            for result in results:
                pair_info = result['pair_info']
                target_symbol = ''.join(c for c in pair_info['target_token'] if ord(c) < 128)
                paired_symbol = ''.join(c for c in pair_info['paired_token'] if ord(c) < 128)
                
                f.write(f"Pair Address: {result['pair_address']}\n")
                f.write(f"Token Pair: {target_symbol}/{paired_symbol}\n")
                f.write(f"Current Price in {paired_symbol}: {pair_info['price_native']}\n")
                if pair_info['price_usd']:
                    f.write(f"Current USD Price: ${pair_info['price_usd']:.10f}\n")
                f.write(f"\nExperimental {paired_symbol} Price: ${result['experimental_paired_price']:.10f}\n")
                f.write(f"Calculated Future Price: ${result['new_hearts_law_price']:.10f}\n")
                f.write(f"Potential X: {result['potential_x']:.2f}x\n")
                f.write("\n" + "-" * 50 + "\n\n")

            # If there was existing content, add a separator and append it
            if existing_content:
                f.write("PREVIOUS ANALYSES\n")
                f.write("-" * 50 + "\n\n")
                f.write(existing_content)

        print(f"\nAnalysis results saved to {filename}")
        
    except Exception as e:
        print(f"Warning: Could not save results to file due to: {e}")
        print("However, the calculations were successful as shown above.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python hearts-law-sim.py <token_name> <pair_address1> [pair_address2 ...]")
        sys.exit(1)

    token_name = sys.argv[1]
    pair_addresses = sys.argv[2:]

    hearts_law_sim(token_name, pair_addresses)
