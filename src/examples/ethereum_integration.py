#!/usr/bin/env python3
"""
ZeroCompress Ethereum Integration Example

This script demonstrates how to use the ZeroCompress library with
real Ethereum transaction data fetched from a node or provider.

It shows how to:
1. Fetch real transaction data from an Ethereum node/provider
2. Train the compressor on historical transactions
3. Apply compression to new transactions
4. Estimate gas savings for L2 rollups
"""

import os
import json
import time
from typing import Dict, List, Any
from web3 import Web3
from web3.providers.rpc import HTTPProvider
import argparse

# Import the ZeroCompress library
from compression import ZeroCompressor
from compression import AddressCompressor, ZeroByteCompressor
from compression import FunctionSelectorCompressor, CalldataCompressor

# Default Ethereum RPC URL (using Infura as an example)
# Replace with your own provider URL or use a command-line argument
DEFAULT_RPC_URL = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"

def fetch_transactions(w3: Web3, block_numbers: List[int]) -> List[Dict[str, Any]]:
    """
    Fetch transactions from specific blocks
    
    Args:
        w3: Web3 instance
        block_numbers: List of block numbers to fetch
        
    Returns:
        List of transaction dictionaries
    """
    all_transactions = []
    
    for block_num in block_numbers:
        print(f"Fetching block {block_num}...")
        try:
            # Get block with transaction data
            block = w3.eth.get_block(block_num, full_transactions=True)
            
            # Extract transactions
            transactions = block.transactions
            
            # Convert to dictionaries and filter for contract calls
            for tx in transactions:
                tx_dict = dict(tx)
                
                # Only include transactions with non-empty input data
                if tx_dict.get('input') and tx_dict.get('input') != '0x':
                    # Convert hexbytes to hex strings for JSON serialization
                    for k, v in tx_dict.items():
                        if isinstance(v, bytes):
                            tx_dict[k] = v.hex()
                            # Ensure '0x' prefix
                            if k in ['input', 'to', 'from'] and not tx_dict[k].startswith('0x'):
                                tx_dict[k] = '0x' + tx_dict[k]
                    
                    all_transactions.append(tx_dict)
            
            print(f"  Found {len(transactions)} transactions in block, "
                  f"{len([tx for tx in transactions if tx.get('input') != '0x'])} with contract calls")
            
        except Exception as e:
            print(f"Error fetching block {block_num}: {e}")
    
    return all_transactions

def estimate_l2_savings(transactions: List[Dict[str, Any]], compressor: ZeroCompressor) -> Dict[str, Any]:
    """
    Estimate gas savings for L2 rollups using ZeroCompress
    
    Args:
        transactions: List of transaction dictionaries
        compressor: Trained ZeroCompressor instance
        
    Returns:
        Dictionary of savings statistics
    """
    original_bytes = 0
    compressed_bytes = 0
    tx_count = 0
    
    # Typical L2 calldata cost in gas
    CALLDATA_COST_PER_BYTE = 16  # Arbitrum/Optimism uses ~16 gas per byte for L1 data
    
    for tx in transactions:
        if tx.get('input') and tx.get('input') != '0x':
            tx_count += 1
            
            # Calculate original size
            input_data = tx['input']
            if input_data.startswith('0x'):
                input_data = input_data[2:]
            
            original_size = len(bytes.fromhex(input_data))
            original_bytes += original_size
            
            # Compress transaction
            compressed_tx = compressor.compress_transaction(tx)
            compressed_input = compressed_tx['input']
            
            if compressed_input.startswith('0x'):
                compressed_input = compressed_input[2:]
            
            compressed_size = len(bytes.fromhex(compressed_input))
            compressed_bytes += compressed_size
    
    # Calculate statistics
    bytes_saved = original_bytes - compressed_bytes
    compression_ratio = 1 - (compressed_bytes / original_bytes) if original_bytes > 0 else 0
    
    # Gas savings
    gas_original = original_bytes * CALLDATA_COST_PER_BYTE
    gas_compressed = compressed_bytes * CALLDATA_COST_PER_BYTE
    gas_saved = gas_original - gas_compressed
    
    # Ethereum mainnet gas prices (in gwei)
    avg_gas_price = 20  # Example average gas price in gwei
    
    # ETH cost savings (assuming 1 ETH = $3000)
    eth_saved = gas_saved * (avg_gas_price / 1e9)
    usd_saved = eth_saved * 3000
    
    return {
        'transactions_analyzed': tx_count,
        'original_bytes': original_bytes,
        'compressed_bytes': compressed_bytes,
        'bytes_saved': bytes_saved,
        'compression_ratio': compression_ratio,
        'gas_saved': gas_saved,
        'eth_saved': eth_saved,
        'usd_saved': usd_saved,
        'avg_savings_per_tx': {
            'bytes': bytes_saved / tx_count if tx_count > 0 else 0,
            'gas': gas_saved / tx_count if tx_count > 0 else 0,
            'eth': eth_saved / tx_count if tx_count > 0 else 0,
            'usd': usd_saved / tx_count if tx_count > 0 else 0
        }
    }

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='ZeroCompress Ethereum Integration Example')
    parser.add_argument('--rpc-url', default=DEFAULT_RPC_URL, 
                        help='Ethereum RPC URL (default: Infura mainnet)')
    parser.add_argument('--blocks', type=int, nargs='+', 
                        help='Block numbers to analyze (default: latest 5 blocks)')
    parser.add_argument('--train-blocks', type=int, default=3,
                        help='Number of blocks to use for training (default: 3)')
    parser.add_argument('--output', default='ethereum_compression_results.json',
                        help='Output file for results (default: ethereum_compression_results.json)')
    args = parser.parse_args()
    
    # Connect to Ethereum node
    try:
        print(f"Connecting to Ethereum node at {args.rpc_url}...")
        w3 = Web3(HTTPProvider(args.rpc_url))
        
        if not w3.is_connected():
            print("Failed to connect to Ethereum node. Check your RPC URL.")
            return
        
        print(f"Connected. Current block: {w3.eth.block_number}")
    except Exception as e:
        print(f"Error connecting to Ethereum node: {e}")
        return
    
    # Determine which blocks to analyze
    if args.blocks:
        block_numbers = args.blocks
    else:
        # Use the latest blocks
        current_block = w3.eth.block_number
        block_numbers = list(range(current_block - 4, current_block + 1))
    
    print(f"Analyzing blocks: {block_numbers}")
    
    # Fetch transactions
    all_transactions = fetch_transactions(w3, block_numbers)
    print(f"Fetched {len(all_transactions)} transactions with contract calls")
    
    if not all_transactions:
        print("No transactions to analyze. Exiting.")
        return
    
    # Split into training and evaluation sets
    if args.train_blocks < len(block_numbers):
        # Calculate the split point based on the number of training blocks
        split_idx = len(all_transactions) * args.train_blocks // len(block_numbers)
        training_txs = all_transactions[:split_idx]
        evaluation_txs = all_transactions[split_idx:]
    else:
        # Use all transactions for both training and evaluation
        training_txs = all_transactions
        evaluation_txs = all_transactions
    
    print(f"Using {len(training_txs)} transactions for training and {len(evaluation_txs)} for evaluation")
    
    # Create and train ZeroCompressor
    print("Training ZeroCompressor on historical transactions...")
    compressor = ZeroCompressor()
    compressor.train_on_transactions(training_txs)
    
    # Estimate savings on evaluation set
    print("Estimating L2 savings on evaluation transactions...")
    savings = estimate_l2_savings(evaluation_txs, compressor)
    
    # Display results
    print("\nCompression Results:")
    print(f"Transactions analyzed: {savings['transactions_analyzed']}")
    print(f"Original size: {savings['original_bytes']} bytes")
    print(f"Compressed size: {savings['compressed_bytes']} bytes")
    print(f"Bytes saved: {savings['bytes_saved']} bytes")
    print(f"Compression ratio: {savings['compression_ratio']:.2f} ({savings['compression_ratio']*100:.1f}%)")
    
    print("\nEstimated L2 Cost Savings:")
    print(f"Gas saved: {savings['gas_saved']:,.0f} gas")
    print(f"ETH saved: {savings['eth_saved']:.6f} ETH")
    print(f"USD saved: ${savings['usd_saved']:,.2f} (at $3000/ETH)")
    
    print("\nAverage Savings Per Transaction:")
    avg = savings['avg_savings_per_tx']
    print(f"Bytes: {avg['bytes']:.1f} bytes")
    print(f"Gas: {avg['gas']:.1f} gas")
    print(f"ETH: {avg['eth']:.6f} ETH")
    print(f"USD: ${avg['usd']:.4f}")
    
    # Save compression statistics
    stats = compressor.get_stats()
    stats['l2_savings'] = savings
    
    # Save results to file
    with open(args.output, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nResults saved to {args.output}")
    
    # Save dictionaries for future use
    if not os.path.exists('dictionaries'):
        os.makedirs('dictionaries')
    
    compressor.save_config('dictionaries/ethereum_compression_config.json')
    print("Compression dictionaries saved to 'dictionaries/ethereum_compression_config.json'")
    
    print("\nExample completed.")

if __name__ == "__main__":
    main() 