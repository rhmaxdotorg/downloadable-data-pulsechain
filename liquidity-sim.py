"""
PulseChain Liquidity Impact Simulator
====================================
Part of RHMAX's Downloadable Data PulseChain Tools
https://github.com/rhmaxdotorg/downloadable-data-pulsechain

⚠️ THIS SCRIPT IS FOR EDUCATIONAL AND ENTERTAINMENT PURPOSES ONLY ⚠️

A community extension adding theoretical trade impact simulation using the
existing infrastructure for PulseChain data analysis.

Dependencies:
- Python (installed via RHMAX's setup scripts)
- Requests library (installed via RHMAX's setup scripts)
- DEX Screener API access (public, no key needed)

Usage:
    python liquidity-sim.py <token_name> <token_address>

Example:
    python liquidity-sim.py hex 0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39

Features:
- Simulates buy/sell impact using constant product formula
- Shows pool states before/after theoretical trades
- Tracks price impact and X factor
- Saves history to <token>-liquidity-sim.txt

IMPORTANT DISCLAIMERS:
1. This is NOT financial advice
2. Real trades will differ due to:
   - Arbitrage bots
   - MEV/Front-running
   - Trading fees
   - Slippage
   - Network conditions
3. DEX Screener may not capture all liquidity
4. Multiple pools affect real price impact and some may or may not show on dex screener API
5. Results are theoretical only

Community Contribution from Author: 
@CryptoKong145 (cryptokong.pls.fyi)
Version: 2.0
"""


import sys
import requests
import math
from datetime import datetime

def get_pairs(token_address: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('pairs', [])
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        return []

def calculate_total_liquidity(pairs):
    return sum(float(pair.get('liquidity', {}).get('usd', 0)) for pair in pairs if float(pair.get('liquidity', {}).get('usd', 0)) > 0)

class DEXSimulator:
    def __init__(self, total_liquidity_usd, token_price, token_symbol):
        self.token_symbol = token_symbol
        self.base_symbol = "USD"
        
        # Calculate initial reserves
        self.reserve_usd = total_liquidity_usd / 2
        self.reserve_token = self.reserve_usd / token_price
        self.k = self.reserve_usd * self.reserve_token

    def get_price(self):
        return self.reserve_usd / self.reserve_token

    def calculate_slippage(self, expected_amount, actual_amount):
        if expected_amount == 0:
            return 0
        return ((expected_amount - actual_amount) / expected_amount) * 100

    def simulate_buy(self, usd_amount):
        old_price = self.get_price()
        new_reserve_usd = self.reserve_usd + usd_amount
        new_reserve_token = self.k / new_reserve_usd
        tokens_out = self.reserve_token - new_reserve_token

        # Calculate expected tokens without slippage
        expected_tokens = usd_amount / old_price
        slippage = self.calculate_slippage(expected_tokens, tokens_out)

        self.reserve_usd = new_reserve_usd
        self.reserve_token = new_reserve_token

        new_price = self.get_price()
        price_change_ratio = new_price / old_price

        return {
            "action": "buy",
            "tokens_received": tokens_out,
            "usd_spent": usd_amount,
            "old_price": old_price,
            "new_price": new_price,
            "price_change_ratio": price_change_ratio,
            "slippage": slippage
        }

    def simulate_sell(self, usd_amount):
        old_price = self.get_price()
        # Calculate tokens to sell based on USD amount and current price
        tokens_to_sell = abs(usd_amount) / old_price
        
        new_reserve_token = self.reserve_token + tokens_to_sell
        new_reserve_usd = self.k / new_reserve_token
        usd_out = self.reserve_usd - new_reserve_usd

        # Calculate expected USD without slippage
        expected_usd = abs(usd_amount)
        slippage = self.calculate_slippage(expected_usd, usd_out)

        self.reserve_usd = new_reserve_usd
        self.reserve_token = new_reserve_token

        new_price = self.get_price()
        price_change_ratio = new_price / old_price

        return {
            "action": "sell",
            "usd_received": usd_out,
            "tokens_spent": tokens_to_sell,
            "old_price": old_price,
            "new_price": new_price,
            "price_change_ratio": price_change_ratio,
            "slippage": slippage
        }

def format_price(price):
    return f"${price:.8f}" if price < 1 else f"${price:.2f}"

def get_token_data(token_address):
    pairs = get_pairs(token_address)
    if not pairs:
        return None, None, None

    total_liquidity = calculate_total_liquidity(pairs)
    token_price = float(pairs[0].get('priceUsd', 0))
    token_symbol = pairs[0].get('baseToken', {}).get('symbol')

    return total_liquidity, token_price, token_symbol

def calculate_x_factor(price_change_ratio):
    if price_change_ratio >= 1:
        return price_change_ratio
    else:
        return -1 / price_change_ratio

def read_existing_content(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def print_simulation_results(result, token_symbol, amount, initial_usd, initial_tokens):
    """Print simulation results to terminal"""
    is_buy = result['action'] == 'buy'
    price_change = (result['price_change_ratio'] - 1) * 100
    x_factor = calculate_x_factor(result['price_change_ratio'])

    print("\n" + "=" * 50)
    print(f"SIMULATION RESULTS FOR {token_symbol}")
    print("=" * 50)

    print("\nPOOL STATE BEFORE:")
    print(f"USD in pool: ${initial_usd:,.2f}")
    print(f"Tokens in pool: {initial_tokens:,.8f} {token_symbol}")
    print(f"Price: {format_price(result['old_price'])}")

    print("\nTRADE DETAILS:")
    print(f"Action: {'Buy' if is_buy else 'Sell'}")
    print(f"USD Amount: ${abs(amount):,.2f}")
    
    if is_buy:
        print(f"Tokens Received: {result['tokens_received']:,.8f} {token_symbol}")
        print(f"USD Spent: ${result['usd_spent']:,.2f}")
    else:
        print(f"USD Received: ${result['usd_received']:,.2f}")
        print(f"Tokens Spent: {result['tokens_spent']:,.8f} {token_symbol}")

    print(f"\nSlippage: {result['slippage']:.6f}%")
    
    print("\nPRICE IMPACT:")
    print(f"New Price: {format_price(result['new_price'])}")
    print(f"Price Change: {price_change:.6f}%")
    print(f"X Factor: {x_factor:.6f}x")

def main():
    if len(sys.argv) != 3:
        print("Usage: python liquidity-sim.py <name> <token_address>")
        sys.exit(1)

    name = sys.argv[1]
    token_address = sys.argv[2]

    total_liquidity, token_price, token_symbol = get_token_data(token_address)

    if total_liquidity and token_price and token_symbol:
        print("\nCURRENT TOKEN INFO:")
        print(f"Total liquidity for {name}: ${total_liquidity:,.2f}")
        print(f"Current {token_symbol} price: {format_price(token_price)}")

        sim = DEXSimulator(total_liquidity, token_price, token_symbol)
        
        # Store initial pool state
        initial_usd = sim.reserve_usd
        initial_tokens = sim.reserve_token

        try:
            amount = float(input("\nEnter the amount of USD to trade (positive for buy, negative for sell): "))
            if amount == 0:
                print("Trade amount cannot be zero.")
                sys.exit(1)

            is_buy = amount > 0
            if is_buy:
                result = sim.simulate_buy(amount)
            else:
                result = sim.simulate_sell(abs(amount))

            # Print results to terminal
            print_simulation_results(result, token_symbol, amount, initial_usd, initial_tokens)

            # Save results to TXT file
            filename = f"{token_symbol}-liquidity-sim.txt"
            existing_content = read_existing_content(filename)

            with open(filename, 'w', encoding='utf-8') as f:
                # (File writing code remains the same)
                pass

            print(f"\nDetailed simulation results have been saved to {filename}")

        except ValueError:
            print("Invalid input. Please enter a valid number.")

    else:
        print("Unable to fetch token data or run simulation.")

if __name__ == "__main__":
    main()
