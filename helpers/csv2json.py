#!/usr/bin/env python3
# Convert CSV to JSON for PulseChain Scripts output
#
# Note: this should be updated with the latest format and structure of scripts if they change
#

import sys
import csv
import json
import os
from collections import defaultdict

def infer_structure(rows):
    if len(rows[0]) == 2:
        return 'token_holders'
    elif len(rows[0]) == 5:
        return 'contract_txs'
    elif len(rows[0]) == 3:
        # This could be either 'contract_calls' or 'common_holding'
        # We'll assume it's 'contract_calls' if the second column isn't an address
        if not rows[0][1].startswith('0x'):
            return 'contract_calls'
        else:
            return 'common_holding'
    elif len(rows[0]) == 5:
        return 'token_liquidity'
    else:
        return 'unknown'

def process_data(rows, structure):
    if structure == 'token_holders':
        return [{'address': row[0], 'amount': row[1]} for row in rows]
    elif structure == 'contract_txs':
        return [{'tx_hash': row[0], 'method': row[1], 'from': row[2], 'to': row[3], 'value': row[4]} for row in rows]
    elif structure == 'contract_calls':
        return [{'wallet': row[0], 'method': row[1], 'amount': row[2]} for row in rows]
    elif structure == 'token_liquidity':
        return [{'dex': row[0], 'LP': row[1], 'token': row[2], 'pair': row[3], 'value': row[4]} for row in rows]
    elif structure == 'common_holding':
        return [{'token': row[0], 'address': row[1], 'number': row[2]} for row in rows]
    else:
        return [dict(zip([f'column_{i}' for i in range(len(row))], row)) for row in rows]

def csv_to_json(csv_file_path):
    # Construct the output JSON file path
    json_file_path = os.path.splitext(csv_file_path)[0] + '.json'
    
    # Read the CSV file
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        rows = list(csv_reader)

    # Infer the structure of the data
    structure = infer_structure(rows)

    # Process the data based on the inferred structure
    data = process_data(rows, structure)
    
    # Write to JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    print(f"Converted {csv_file_path} to {json_file_path}")
    print(f"Inferred structure: {structure}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <csv_file_path>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    csv_to_json(csv_file_path)
