#!/usr/bin/env python3
"""
ZeroCompress Transaction Data Collector

This script collects transaction data from L2 networks (Arbitrum, Optimism, Base)
for analysis of compression patterns.
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import requests
import pandas as pd
from web3 import Web3
from web3.types import TxData, BlockData
from tqdm import tqdm
from eth_utils import to_hex, to_bytes, encode_hex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("transaction_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Network configurations
NETWORK_CONFIGS = {
    "arbitrum": {
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "explorer_api": "https://api.arbiscan.io/api",
        "chain_id": 42161,
        "block_time": 0.5,  # approximate, in seconds
        "explorer_api_key": "",  # Add your API key here
    },
    "optimism": {
        "rpc_url": "https://mainnet.optimism.io",
        "explorer_api": "https://api-optimistic.etherscan.io/api",
        "chain_id": 10,
        "block_time": 2,  # approximate, in seconds
        "explorer_api_key": "",  # Add your API key here
    },
    "base": {
        "rpc_url": "https://mainnet.base.org",
        "explorer_api": "https://api.basescan.org/api",
        "chain_id": 8453,
        "block_time": 2,  # approximate, in seconds
        "explorer_api_key": "",  # Add your API key here
    }
}

# Transaction type classification
FUNCTION_SIGNATURES = {
    # ERC20 Transfer
    "0xa9059cbb": "erc20_transfer",
    # ERC20 Approve
    "0x095ea7b3": "erc20_approve",
    # ERC20 TransferFrom
    "0x23b872dd": "erc20_transferFrom",
    # ERC721 Transfer
    "0x23b872dd": "erc721_transferFrom",
    # ERC721 SafeTransfer
    "0x42842e0e": "erc721_safeTransferFrom",
    # Uniswap V2 Swap
    "0x7ff36ab5": "uniswap_swapExactETHForTokens",
    "0x38ed1739": "uniswap_swapExactTokensForTokens",
    # Uniswap V3 Swap
    "0x5ae401dc": "uniswap_multicall",
    # 1inch Swap
    "0x7c025200": "oneinch_swap",
    # Other common function signatures
    "0x": "eth_transfer",  # Empty data is an ETH transfer
}

class TransactionCollector:
    def __init__(self, network: str, output_dir: str):
        """Initialize the transaction collector for a specific network"""
        self.network = network
        self.output_dir = output_dir
        
        if network not in NETWORK_CONFIGS:
            raise ValueError(f"Unsupported network: {network}. Supported networks: {list(NETWORK_CONFIGS.keys())}")
        
        config = NETWORK_CONFIGS[network]
        self.rpc_url = config["rpc_url"]
        self.explorer_api = config["explorer_api"]
        self.chain_id = config["chain_id"]
        self.block_time = config["block_time"]
        self.explorer_api_key = config["explorer_api_key"]
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Check connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {network} RPC at {self.rpc_url}")
        
        logger.info(f"Connected to {network} at {self.rpc_url}, chain ID: {self.w3.eth.chain_id}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create network-specific directory
        self.network_dir = os.path.join(output_dir, network)
        os.makedirs(self.network_dir, exist_ok=True)
    
    def collect_blocks(self, start_block: int, num_blocks: int) -> List[BlockData]:
        """Collect block data for a range of blocks"""
        blocks = []
        current_block = start_block
        end_block = start_block + num_blocks
        
        logger.info(f"Collecting {num_blocks} blocks from {start_block} to {end_block-1}")
        
        with tqdm(total=num_blocks, desc=f"Collecting blocks from {self.network}") as pbar:
            while current_block < end_block:
                try:
                    block = self.w3.eth.get_block(current_block, full_transactions=True)
                    blocks.append(block)
                    current_block += 1
                    pbar.update(1)
                    
                    # Rate limiting to avoid overloading the RPC
                    time.sleep(0.1)  
                except Exception as e:
                    logger.error(f"Error retrieving block {current_block}: {e}")
                    time.sleep(2)  # Wait longer on error
        
        return blocks
    
    def collect_transactions(self, blocks: List[BlockData]) -> List[Dict[str, Any]]:
        """Extract and process transaction data from blocks"""
        transactions = []
        
        logger.info(f"Processing transactions from {len(blocks)} blocks")
        
        for block in tqdm(blocks, desc="Processing blocks"):
            for tx in block.transactions:
                try:
                    # Convert TxData to dict
                    if isinstance(tx, (dict, TxData)):
                        tx_dict = dict(tx)
                    else:
                        # If it's a HexBytes or other format, get it by hash
                        tx_dict = dict(self.w3.eth.get_transaction(tx))
                    
                    tx_dict = self._process_transaction(tx_dict, block)
                    if tx_dict:
                        transactions.append(tx_dict)
                except Exception as e:
                    logger.error(f"Error processing transaction {tx.hash if hasattr(tx, 'hash') else 'unknown'}: {e}")
        
        return transactions
    
    def _process_transaction(self, tx: Dict[str, Any], block: BlockData) -> Dict[str, Any]:
        """Process a transaction to extract relevant data"""
        # Convert HexBytes to hex strings for easy storage
        processed_tx = {}
        
        for key, value in tx.items():
            if key in ['chainId', 'gas', 'gasPrice', 'nonce', 'v', 'blockNumber']:
                processed_tx[key] = int(value) if value is not None else None
            elif key in ['value', 'maxFeePerGas', 'maxPriorityFeePerGas']:
                processed_tx[key] = str(value) if value is not None else None
            elif key in ['to', 'from']:
                processed_tx[key] = value.lower() if value is not None else None
            elif isinstance(value, (bytes, bytearray)):
                processed_tx[key] = to_hex(value)
            else:
                processed_tx[key] = value
        
        # Add timestamp from block
        processed_tx['timestamp'] = block.timestamp
        
        # Classify transaction type
        processed_tx['type'] = self._classify_transaction(processed_tx)
        
        # Add calldata size
        input_data = processed_tx.get('input', '') or ''
        processed_tx['calldata_size'] = len(input_data) // 2 - 1 if input_data.startswith('0x') else len(input_data) // 2
        
        # Add zero-byte analysis
        processed_tx['zero_bytes'] = self._count_zero_bytes(input_data)
        processed_tx['zero_byte_percentage'] = processed_tx['zero_bytes'] / processed_tx['calldata_size'] if processed_tx['calldata_size'] > 0 else 0
        
        return processed_tx
    
    def _classify_transaction(self, tx: Dict[str, Any]) -> str:
        """Classify transaction by type based on input data"""
        input_data = tx.get('input', '')
        
        # If no input data or empty, it's an ETH transfer
        if not input_data or input_data == '0x':
            return 'eth_transfer'
        
        # Extract function signature (first 4 bytes after 0x)
        if input_data.startswith('0x') and len(input_data) >= 10:
            function_sig = input_data[0:10].lower()
            
            # Check known signatures
            if function_sig in FUNCTION_SIGNATURES:
                return FUNCTION_SIGNATURES[function_sig]
        
        # Check for contract deployment
        if tx.get('to') is None:
            return 'contract_deployment'
        
        return 'contract_interaction'
    
    def _count_zero_bytes(self, hex_data: str) -> int:
        """Count zero bytes in hex data"""
        if not hex_data or hex_data == '0x':
            return 0
        
        if hex_data.startswith('0x'):
            hex_data = hex_data[2:]
        
        # Count 00 sequences in hex string
        count = 0
        for i in range(0, len(hex_data), 2):
            if i+1 < len(hex_data) and hex_data[i:i+2] == '00':
                count += 1
        
        return count
    
    def save_transactions(self, transactions: List[Dict[str, Any]], filename: str = None) -> str:
        """Save transactions to a file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.network}_transactions_{timestamp}.json"
        
        output_path = os.path.join(self.network_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(transactions, f, indent=2)
        
        logger.info(f"Saved {len(transactions)} transactions to {output_path}")
        return output_path
    
    def analyze_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform basic analysis on transactions"""
        if not transactions:
            return {}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(transactions)
        
        # Transaction type distribution
        type_counts = df['type'].value_counts().to_dict()
        
        # Calldata size statistics
        calldata_stats = {
            'mean': df['calldata_size'].mean(),
            'median': df['calldata_size'].median(),
            'min': df['calldata_size'].min(),
            'max': df['calldata_size'].max(),
            'total': df['calldata_size'].sum(),
        }
        
        # Zero byte statistics
        zero_byte_stats = {
            'mean_percentage': df['zero_byte_percentage'].mean() * 100,
            'median_percentage': df['zero_byte_percentage'].median() * 100,
            'total_zero_bytes': df['zero_bytes'].sum(),
            'potential_savings': df['zero_bytes'].sum() / df['calldata_size'].sum() * 100,
        }
        
        # Statistics by transaction type
        type_stats = {}
        for tx_type in df['type'].unique():
            type_df = df[df['type'] == tx_type]
            type_stats[tx_type] = {
                'count': len(type_df),
                'avg_calldata_size': type_df['calldata_size'].mean(),
                'total_calldata_size': type_df['calldata_size'].sum(),
                'avg_zero_byte_percentage': type_df['zero_byte_percentage'].mean() * 100,
            }
        
        return {
            'transaction_count': len(transactions),
            'type_distribution': type_counts,
            'calldata_stats': calldata_stats,
            'zero_byte_stats': zero_byte_stats,
            'type_stats': type_stats,
        }
    
    def save_analysis(self, analysis: Dict[str, Any], filename: str = None) -> str:
        """Save analysis results to a file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.network}_analysis_{timestamp}.json"
        
        output_path = os.path.join(self.network_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Saved analysis to {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description='Collect and analyze transaction data from L2 networks')
    parser.add_argument('--network', type=str, choices=list(NETWORK_CONFIGS.keys()), required=True,
                        help='Network to collect data from')
    parser.add_argument('--output-dir', type=str, default='./data',
                        help='Directory to save output files')
    parser.add_argument('--start-block', type=int, default=None,
                        help='Starting block number (default: latest block - 100)')
    parser.add_argument('--num-blocks', type=int, default=100,
                        help='Number of blocks to collect (default: 100)')
    
    args = parser.parse_args()
    
    try:
        collector = TransactionCollector(args.network, args.output_dir)
        
        # If start block not specified, use latest block - num_blocks
        if args.start_block is None:
            latest_block = collector.w3.eth.block_number
            args.start_block = max(0, latest_block - args.num_blocks)
        
        # Collect block data
        blocks = collector.collect_blocks(args.start_block, args.num_blocks)
        
        # Extract and process transactions
        transactions = collector.collect_transactions(blocks)
        
        # Save transactions
        collector.save_transactions(transactions)
        
        # Analyze transactions
        analysis = collector.analyze_transactions(transactions)
        
        # Save analysis
        collector.save_analysis(analysis)
        
        logger.info(f"Successfully collected and analyzed {len(transactions)} transactions from {args.network}")
        
    except Exception as e:
        logger.error(f"Error in data collection: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 