#!/usr/bin/env python3
#
# Scan for burned tokens on PulseChain by directly checking burn address balances
#
# Example usage:
# $ ./get-burned-tokens.py <token_name> <token_address>
#

import sys
import requests
from decimal import Decimal
from web3 import Web3

# PulseChain RPC endpoint
RPC_ENDPOINT = "https://rpc.pulsechain.com"

# Blockscout API endpoint
SCAN_API = "https://api.scan.pulsechain.com/api/v2/"

# Burn addresses
BURN_ADDRESSES = [
    "0x0000000000000000000000000000000000000000",  # Zero address
    "0x000000000000000000000000000000000000dEaD",  # Dead address
]

# ERC20 ABI (only the functions we need)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# not sure as of now on how to get an accurate PLS supply either via blockchain or API
def get_pls_supply():
    return 'TBD'

def scan_burned_tokens(name, token_address=None):
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))

    if not w3.is_connected():
        print("Failed to connect to the PulseChain network. Please check your internet connection and try again.")
        return

    is_native_token = name.lower() == "pls"

    if is_native_token:
        name = "PulseChain"
        token_symbol = "PLS"
        token_decimals = 18
        total_supply = get_pls_supply()
        if total_supply is None:
            print("Failed to fetch PLS supply")
            return
    else:
        if not token_address:
            print("Token address is required for non-PLS tokens.")
            return
        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        try:
            name = token_contract.functions.name().call()
            token_symbol = token_contract.functions.symbol().call()
            token_decimals = token_contract.functions.decimals().call()
            total_supply = token_contract.functions.totalSupply().call()
        except Exception as e:
            print(f"Error fetching token information: {e}")
            return

    total_burned = 0
    burn_details = []

    for burn_address in BURN_ADDRESSES:
        try:
            if is_native_token:
                balance = w3.eth.get_balance(burn_address)
            else:
                balance = token_contract.functions.balanceOf(burn_address).call()
            total_burned += balance
            if balance > 0:
                burn_details.append(f"{burn_address}: {balance / (10 ** token_decimals):,.2f}")
        except Exception as e:
            print(f"Error fetching balance for {burn_address}: {e}")

    total_burned_decimal = Decimal(total_burned) / Decimal(10 ** token_decimals)

    if not is_native_token:
        total_supply_decimal = Decimal(total_supply) / Decimal(10 ** token_decimals)
        burn_percentage = (total_burned_decimal / total_supply_decimal) * 100 if total_supply_decimal > 0 else 0

    print(f"\nResults for {name} ({token_symbol}):")

    if not is_native_token:
        print(f"Token Address: {token_address}")
        print(f"Total Supply: {total_supply_decimal:,.2f}")
    else:
        print(f"Total Supply: {total_supply}")

    print(f"Total Burned: {total_burned_decimal:,.2f}")

    if not is_native_token:
        print(f"Burn Percentage: {burn_percentage:.2f}%")

    if burn_details:
        print("\nBurn Address Details:")
        for detail in burn_details:
            print(detail)
    else:
        print("\nNo tokens found in burn addresses.")

    # write_to_csv(name, token_address if not is_native_token else "PLS", total_burned_decimal)
    write_to_csv(token_symbol, token_address if not is_native_token else "PLS", total_burned_decimal)

def write_to_csv(name, token_address, total_burned):
    filename = f"{name.lower()}-burned.txt"
    with open(filename, 'w') as f:
        f.write(f"{name.lower()},{token_address},{int(total_burned)}")
    # print(f"CSV output written to {filename}")

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <name> [token_address]")
        print("Note: For PLS (native token), token_address is not required.")
        sys.exit(1)

    name = sys.argv[1]
    token_address = sys.argv[2] if len(sys.argv) == 3 else None

    try:
        scan_burned_tokens(name, token_address)
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
