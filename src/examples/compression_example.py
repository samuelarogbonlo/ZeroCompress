#!/usr/bin/env python3
"""
ZeroCompress Example Script

This script demonstrates the usage of the ZeroCompress library for
compressing and decompressing Ethereum transaction data.

It shows how to:
1. Train the compressor on sample data
2. Compress transaction calldata
3. Decompress it back to the original form
4. View compression statistics
"""

import os
import json
import binascii
from typing import Dict, List, Any

# Import the ZeroCompress library
from compression import ZeroCompressor
from compression import AddressCompressor, ZeroByteCompressor
from compression import FunctionSelectorCompressor, CalldataCompressor

# Sample transaction data (simplified for demonstration)
SAMPLE_TRANSACTIONS = [
    {
        "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC contract
        "input": "0xa9059cbb000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000000000005f5e100"  # transfer(address,uint256)
    },
    {
        "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC contract
        "input": "0xa9059cbb000000000000000000000000d13c4077a4a8e3b809728aa8989cbd3e7c8f96d70000000000000000000000000000000000000000000000000000000002faf080"  # transfer(address,uint256)
    },
    {
        "from": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "to": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap router
        "input": "0x7ff36ab5000000000000000000000000000000000000000000000003884d387e2eda1f000000000000000000000000000000000000000000000000000000000000008000000000000000000000000028c6c06298d514db089934071355e5743bf21d60000000000000000000000000000000000000000000000000000000064a97b530000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000635fe0ba427edfc9da134340be7ecc35c4a967c2"  # swapExactETHForTokens
    },
    {
        "from": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "to": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH contract
        "input": "0x2e1a7d4d0000000000000000000000000000000000000000000000000de0b6b3a7640000"  # withdraw(uint256)
    },
    {
        "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC contract
        "input": "0xa9059cbb0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # transfer with zero address and zero amount
    }
]

def hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes"""
    if hex_str.startswith('0x'):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)

def bytes_to_hex(data: bytes) -> str:
    """Convert bytes to hex string"""
    return '0x' + data.hex()

def format_bytes(data: bytes) -> str:
    """Format bytes for display"""
    return bytes_to_hex(data)[:20] + '...' if len(data) > 10 else bytes_to_hex(data)

def main():
    print("ZeroCompress Library Example\n")
    
    # Create a ZeroCompressor instance
    compressor = ZeroCompressor()
    
    # Extract data for training
    addresses = []
    selectors = []
    calldata_samples = []
    
    for tx in SAMPLE_TRANSACTIONS:
        # Extract addresses
        if tx.get('from'):
            addresses.append(tx['from'])
        if tx.get('to'):
            addresses.append(tx['to'])
        
        # Extract calldata
        input_data = tx.get('input', '')
        if input_data and input_data != '0x' and len(input_data) >= 10:
            # Convert to bytes
            calldata = hex_to_bytes(input_data)
            calldata_samples.append(calldata)
            
            # Extract selector (first 4 bytes)
            if len(calldata) >= 4:
                selectors.append(calldata[:4])
    
    # Train component compressors
    print("Training address compressor...")
    address_compressor = AddressCompressor()
    address_compressor.build_dictionary(addresses)
    
    print("Training function selector compressor...")
    selector_compressor = FunctionSelectorCompressor()
    selector_compressor.build_dictionary(selectors)
    
    print("Training calldata pattern compressor...")
    calldata_compressor = CalldataCompressor()
    calldata_compressor.build_dictionary(calldata_samples)
    
    # Train the main compressor on sample transactions
    print("Training main compressor...")
    compressor.train_on_transactions(SAMPLE_TRANSACTIONS)
    
    print("\nCompression Examples:\n")
    print("-" * 80)
    
    # Process each transaction
    for i, tx in enumerate(SAMPLE_TRANSACTIONS):
        print(f"Transaction {i+1}:")
        print(f"  From: {tx['from']}")
        print(f"  To:   {tx['to']}")
        
        # Get original calldata
        original_input = tx.get('input', '0x')
        original_bytes = hex_to_bytes(original_input)
        print(f"  Original calldata ({len(original_bytes)} bytes): {original_input[:50]}...")
        
        # Compress the transaction
        compressed_tx = compressor.compress_transaction(tx)
        
        # Get compressed calldata
        compressed_input = compressed_tx.get('input', '0x')
        compressed_bytes = hex_to_bytes(compressed_input)
        print(f"  Compressed calldata ({len(compressed_bytes)} bytes): {compressed_input[:50]}...")
        
        # Calculate savings
        savings = len(original_bytes) - len(compressed_bytes)
        savings_pct = (savings / len(original_bytes)) * 100 if len(original_bytes) > 0 else 0
        print(f"  Savings: {savings} bytes ({savings_pct:.1f}%)")
        
        # Decompress and verify
        decompressed_tx = compressor.decompress_transaction(compressed_tx)
        decompressed_input = decompressed_tx.get('input', '0x')
        
        # Verify correctness
        if original_input == decompressed_input:
            print("  ✅ Decompression successful - matches original data")
        else:
            print("  ❌ Decompression failed - does not match original data")
        
        print("-" * 80)
    
    # Show overall statistics
    print("\nCompression Statistics:")
    stats = compressor.get_stats()
    
    print(f"Total transactions processed: {stats['total_txs_processed']}")
    print(f"Total bytes processed: {stats['total_bytes_processed']}")
    print(f"Total bytes compressed: {stats['total_bytes_compressed']}")
    
    if stats['total_bytes_processed'] > 0:
        overall_ratio = 1 - (stats['total_bytes_compressed'] / stats['total_bytes_processed'])
        print(f"Overall compression ratio: {overall_ratio:.2f} ({overall_ratio*100:.1f}%)")
    
    # Component statistics
    print("\nCompression Techniques Effectiveness:")
    
    print("Address Compression:")
    addr_stats = stats.get('address_compression', {})
    print(f"  Dictionary size: {addr_stats.get('dictionary_size', 0)} addresses")
    print(f"  Addresses compressed: {addr_stats.get('addresses_compressed', 0)}")
    print(f"  Bytes saved: {addr_stats.get('bytes_saved', 0)}")
    
    print("Function Selector Compression:")
    func_stats = stats.get('function_selector_compression', {})
    print(f"  Dictionary size: {func_stats.get('dictionary_size', 0)} selectors")
    print(f"  Selectors compressed: {func_stats.get('selectors_compressed', 0)}")
    print(f"  Bytes saved: {func_stats.get('bytes_saved', 0)}")
    
    print("Zero Byte Compression:")
    zero_stats = stats.get('zero_byte_compression', {})
    print(f"  Zero bytes found: {zero_stats.get('total_zero_bytes', 0)}")
    print(f"  Sequences compressed: {zero_stats.get('sequences_compressed', 0)}")
    print(f"  Bytes saved: {zero_stats.get('bytes_saved', 0)}")
    
    # Save dictionaries
    if not os.path.exists('dictionaries'):
        os.makedirs('dictionaries')
    
    print("\nSaving compression dictionaries to 'dictionaries/' directory...")
    compressor.save_config('dictionaries/compression_config.json')
    
    print("\nExample completed. You can use the saved dictionaries for future compression.")

if __name__ == "__main__":
    main() 