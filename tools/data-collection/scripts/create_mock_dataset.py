#!/usr/bin/env python3
"""
ZeroCompress Mock Dataset Generator

This script creates a large mock dataset of Ethereum transactions
for testing compression algorithms.
"""

import os
import json
import random
import argparse
from typing import Dict, List, Any
from tqdm import tqdm
from datetime import datetime, timedelta

# Common Ethereum addresses (top addresses by transaction count)
COMMON_ADDRESSES = [
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap Router
    "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",  # Uniswap Factory
    "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9",  # Aave
    "0x242301fa9f9a1e2d0b0f9922ef54031f8e86a1b9",  # JustSwap
    "0x398ec7346dcd622edc5ae82352f02be94c62d119",  # Aave Lending
    "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
    "0x3cb138c1c5bb61c00519dbe7d38b0738c82bf8a1",  # V3swap
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"   # UNI
]

# Common function signatures (hex)
COMMON_SIGNATURES = {
    "0xa9059cbb": "transfer(address,uint256)",               # ERC20 transfer
    "0x095ea7b3": "approve(address,uint256)",                # ERC20 approve
    "0x23b872dd": "transferFrom(address,address,uint256)",   # ERC20/721 transferFrom
    "0x70a08231": "balanceOf(address)",                      # ERC20/721 balanceOf
    "0x18160ddd": "totalSupply()",                           # ERC20 totalSupply
    "0x7ff36ab5": "swapExactETHForTokens(...)",              # Uniswap swap
    "0x38ed1739": "swapExactTokensForTokens(...)",           # Uniswap swap
    "0x5c11d795": "swapExactTokensForTokensSupportingFeeOnTransferTokens(...)",
    "0xe8e33700": "addLiquidity(...)",                       # Uniswap add liquidity
    "0xf305d719": "addLiquidityETH(...)",                    # Uniswap add liquidity ETH
    "0x2e1a7d4d": "withdraw(uint256)",                       # WETH withdraw
    "0xd0e30db0": "deposit()",                               # WETH deposit
    "0x022c0d9f": "swap(...)",                               # Uniswap V2 swap
    "0x8803dbee": "swapTokensForExactTokens(...)",           # Uniswap swap
    "0xfb3bdb41": "swapETHForExactTokens(...)",              # Uniswap swap
    "0x791ac947": "swapExactTokensForETH(...)"               # Uniswap swap
}

# Transaction types
TRANSACTION_TYPES = [
    "erc20_transfer",
    "erc20_approve",
    "erc20_transferFrom",
    "eth_transfer",
    "uniswap_swap",
    "contract_deployment",
    "contract_interaction"
]

def generate_address():
    """Generate a random Ethereum address"""
    if random.random() < 0.7:  # 70% chance of using a common address
        return random.choice(COMMON_ADDRESSES)
    else:
        # Generate a random address
        return "0x" + "".join(random.choice("0123456789abcdef") for _ in range(40))

def generate_value():
    """Generate a random transaction value"""
    # Most transactions are 0 value when interacting with contracts
    if random.random() < 0.7:
        return "0"
    
    # Generate a random value
    magnitude = random.randint(16, 24)  # From wei to thousands of ETH
    value = random.randint(1, 9999) * (10 ** random.randint(1, magnitude))
    return str(value)

def generate_calldata(tx_type):
    """Generate realistic calldata for a transaction type"""
    # Empty calldata for ETH transfers
    if tx_type == "eth_transfer":
        return "0x"
    
    # Choose a function signature based on type
    if tx_type == "erc20_transfer":
        sig = "0xa9059cbb"  # transfer(address,uint256)
    elif tx_type == "erc20_approve":
        sig = "0x095ea7b3"  # approve(address,uint256)
    elif tx_type == "erc20_transferFrom":
        sig = "0x23b872dd"  # transferFrom(address,address,uint256)
    elif tx_type == "uniswap_swap":
        sig = random.choice(["0x7ff36ab5", "0x38ed1739", "0x5c11d795", "0xfb3bdb41"])
    elif tx_type == "contract_deployment":
        # Contract bytecode tends to have lots of zeros and common patterns
        bytecode_len = random.randint(500, 3000)
        bytecode = ""
        for _ in range(bytecode_len):
            if random.random() < 0.4:  # 40% chance of a zero byte
                bytecode += "00"
            else:
                bytecode += "".join(random.choice("0123456789abcdef") for _ in range(2))
        return "0x" + bytecode
    else:  # contract_interaction
        # Random function signature
        sig = random.choice(list(COMMON_SIGNATURES.keys()))
    
    # For normal function calls, add parameters
    if tx_type != "contract_deployment":
        # Add random parameters based on the function type
        if sig == "0xa9059cbb" or sig == "0x095ea7b3":  # transfer or approve
            # address parameter (32 bytes with leading zeros)
            param1 = "000000000000000000000000" + generate_address()[2:]
            # uint256 parameter (32 bytes)
            param2 = ""
            # 40% chance of having many zeros in the value
            if random.random() < 0.4:
                num_zeros = random.randint(10, 20)
                param2 = "0" * num_zeros + "".join(random.choice("0123456789abcdef") for _ in range(64 - num_zeros))
            else:
                param2 = "0" * random.randint(1, 60) + "".join(random.choice("123456789abcdef") for _ in range(4))
            
            calldata = sig + param1 + param2
        elif sig == "0x23b872dd":  # transferFrom
            # 3 parameters: 2 addresses and an amount
            param1 = "000000000000000000000000" + generate_address()[2:]
            param2 = "000000000000000000000000" + generate_address()[2:]
            param3 = "0" * random.randint(1, 60) + "".join(random.choice("123456789abcdef") for _ in range(4))
            calldata = sig + param1 + param2 + param3
        elif tx_type == "uniswap_swap":
            # Uniswap swaps have complex parameters
            # Just generating realistic-looking calldata with lots of zeros
            params_len = random.randint(4, 10) * 64  # 4-10 parameters of 32 bytes each
            params = ""
            for i in range(0, params_len, 64):
                if random.random() < 0.6:  # 60% chance of having many zeros
                    num_zeros = random.randint(40, 60)
                    params += "0" * num_zeros + "".join(random.choice("0123456789abcdef") for _ in range(64 - num_zeros))
                else:
                    params += "".join(random.choice("0123456789abcdef") for _ in range(64))
            calldata = sig + params
        else:
            # Generic parameters for other function calls
            params_len = random.randint(1, 6) * 64  # 1-6 parameters of 32 bytes each
            params = ""
            for i in range(0, params_len, 64):
                if random.random() < 0.5:  # 50% chance of having many zeros
                    num_zeros = random.randint(30, 60)
                    params += "0" * num_zeros + "".join(random.choice("0123456789abcdef") for _ in range(64 - num_zeros))
                else:
                    params += "".join(random.choice("0123456789abcdef") for _ in range(64))
            calldata = sig + params
    else:
        calldata = "0x"  # Should never reach here
    
    return "0x" + calldata

def count_zero_bytes(hex_data: str) -> int:
    """Count zero bytes in hex data"""
    if not hex_data or hex_data == "0x":
        return 0
    
    if hex_data.startswith("0x"):
        hex_data = hex_data[2:]
    
    # Count 00 sequences in hex string
    count = 0
    for i in range(0, len(hex_data), 2):
        if i+1 < len(hex_data) and hex_data[i:i+2] == "00":
            count += 1
    
    return count

def generate_transaction(timestamp):
    """Generate a random transaction with realistic properties"""
    # Choose transaction type with weighted distribution
    tx_type = random.choices(
        TRANSACTION_TYPES, 
        weights=[0.4, 0.15, 0.1, 0.1, 0.15, 0.05, 0.05],  # 40% are ERC20 transfers
        k=1
    )[0]
    
    # For contract deployments, to is None
    to_address = None if tx_type == "contract_deployment" else generate_address()
    
    # Generate calldata
    input_data = generate_calldata(tx_type)
    
    # Calculate calldata size and zero bytes
    calldata_size = len(input_data) // 2 - 1 if input_data.startswith("0x") else len(input_data) // 2
    zero_bytes = count_zero_bytes(input_data)
    zero_byte_percentage = zero_bytes / calldata_size if calldata_size > 0 else 0
    
    return {
        "from": generate_address(),
        "to": to_address,
        "input": input_data,
        "value": generate_value(),
        "type": tx_type,
        "timestamp": timestamp,
        "calldata_size": calldata_size,
        "zero_bytes": zero_bytes,
        "zero_byte_percentage": zero_byte_percentage
    }

def generate_transactions(count: int, output_file: str):
    """Generate a dataset of random transactions"""
    transactions = []
    
    # Start from a recent timestamp and go backward
    timestamp = int(datetime.now().timestamp())
    
    for _ in tqdm(range(count), desc="Generating transactions"):
        # Generate a transaction
        tx = generate_transaction(timestamp)
        transactions.append(tx)
        
        # Decrement timestamp for the next transaction (roughly 2-4 tx per second)
        timestamp -= random.randint(250, 500)
    
    # Save to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(transactions, f, indent=2)
    
    print(f"Generated {count} transactions and saved to {output_file}")
    
    # Basic statistics
    tx_types = {}
    total_bytes = 0
    total_zero_bytes = 0
    
    for tx in transactions:
        tx_type = tx["type"]
        tx_types[tx_type] = tx_types.get(tx_type, 0) + 1
        total_bytes += tx["calldata_size"]
        total_zero_bytes += tx["zero_bytes"]
    
    print("\nTransaction Type Distribution:")
    for tx_type, count in tx_types.items():
        print(f"  {tx_type}: {count} ({count/len(transactions)*100:.1f}%)")
    
    print(f"\nTotal calldata: {total_bytes} bytes")
    print(f"Total zero bytes: {total_zero_bytes} bytes ({total_zero_bytes/total_bytes*100:.1f}%)")
    
    return transactions

def main():
    parser = argparse.ArgumentParser(description="Generate mock Ethereum transaction data")
    parser.add_argument("--output", type=str, default="/Users/samuel/Eth/ZeroCompress/data/mock_transactions.json",
                        help="Output file path")
    parser.add_argument("--count", type=int, default=10000,
                        help="Number of transactions to generate")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
    
    # Generate transactions
    generate_transactions(args.count, args.output)

if __name__ == "__main__":
    main() 