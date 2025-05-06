#!/usr/bin/env python3
"""
ZeroCompress Calldata Pattern Analyzer

This script analyzes calldata patterns in transaction data to evaluate the potential
effectiveness of calldata-specific compression techniques.
"""

import os
import json
import argparse
import logging
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
import re

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("calldata_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Common EVM function signatures
KNOWN_SIGNATURES = {
    # ERC20
    '0xa9059cbb': 'transfer(address,uint256)',
    '0x23b872dd': 'transferFrom(address,address,uint256)',
    '0x095ea7b3': 'approve(address,uint256)',
    '0x70a08231': 'balanceOf(address)',
    '0x18160ddd': 'totalSupply()',
    '0xdd62ed3e': 'allowance(address,address)',
    
    # ERC721
    '0x6352211e': 'ownerOf(uint256)',
    '0xb88d4fde': 'safeTransferFrom(address,address,uint256,bytes)',
    '0x42842e0e': 'safeTransferFrom(address,address,uint256)',
    '0x095ea7b3': 'approve(address,uint256)',
    '0xa22cb465': 'setApprovalForAll(address,bool)',
    
    # Uniswap V2/V3 Common
    '0x38ed1739': 'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)',
    '0xf305d719': 'addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)',
    '0xe8e33700': 'addLiquidityETH(address,uint256,uint256,uint256,address,uint256)',
    
    # Other common functions
    '0x3593564c': 'execute(bytes,bytes[],uint256)',
    '0x4e71d92d': 'claim()',
    '0xc2b12a73': 'execute(bytes32,address,uint256,bytes)',
}

class CalldataPatternAnalyzer:
    def __init__(self, input_file: str, output_dir: str = None):
        """Initialize the calldata pattern analyzer"""
        self.input_file = input_file
        
        # Set output directory
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.dirname(input_file)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load transaction data
        self.transactions = self._load_transactions()
        
        logger.info(f"Loaded {len(self.transactions)} transactions from {input_file}")
    
    def _load_transactions(self) -> List[Dict[str, Any]]:
        """Load transaction data from JSON file"""
        with open(self.input_file, 'r') as f:
            transactions = json.load(f)
        return transactions
    
    def _extract_function_signature(self, input_data: str) -> str:
        """Extract the function signature from calldata"""
        if not input_data or len(input_data) < 10 or not input_data.startswith('0x'):
            return ''
        return input_data[0:10]  # 0x + 8 hex characters (4 bytes)
    
    def _decode_function_signature(self, signature: str) -> str:
        """Try to decode a function signature using the known signatures dictionary"""
        return KNOWN_SIGNATURES.get(signature[2:], signature)
    
    def analyze_function_signatures(self) -> Dict[str, Any]:
        """Analyze function signature patterns in calldata"""
        # Count function signatures
        signature_counts = Counter()
        signature_data_sizes = defaultdict(list)
        total_valid_transactions = 0
        
        for tx in tqdm(self.transactions, desc="Analyzing function signatures"):
            input_data = tx.get('input', '')
            if not input_data or input_data == '0x':
                continue
                
            signature = self._extract_function_signature(input_data)
            if signature:
                signature_counts[signature] += 1
                signature_data_sizes[signature].append(len(input_data) // 2 - 4)  # Size in bytes after the signature
                total_valid_transactions += 1
        
        # Calculate statistics
        signature_stats = {}
        
        for signature, count in signature_counts.most_common():
            if count < 5:  # Skip very rare signatures
                continue
                
            decoded = self._decode_function_signature(signature)
            sizes = signature_data_sizes[signature]
            
            signature_stats[signature] = {
                'count': count,
                'percentage': (count / total_valid_transactions) * 100 if total_valid_transactions > 0 else 0,
                'decoded': decoded,
                'data_size_stats': {
                    'mean': np.mean(sizes),
                    'median': np.median(sizes),
                    'min': min(sizes),
                    'max': max(sizes),
                    'std_dev': np.std(sizes),
                },
                'total_data_bytes': sum(sizes),
            }
        
        return {
            'total_transactions_analyzed': total_valid_transactions,
            'unique_signatures': len(signature_counts),
            'top_signatures': signature_stats,
            'compression_potential': self._estimate_signature_compression(signature_counts, total_valid_transactions)
        }
    
    def _estimate_signature_compression(self, signature_counts: Counter, total_txs: int) -> Dict[str, Any]:
        """Estimate compression potential from function signature patterns"""
        if total_txs == 0:
            return {'bytes_saved_per_tx': 0, 'total_bytes_saved': 0, 'percentage_savings': 0}
        
        # Suppose we use a 1-byte index for common signatures instead of 4 bytes
        # We'd save 3 bytes per transaction for common signatures
        common_signatures = sum(count for signature, count in signature_counts.items() 
                               if count > total_txs * 0.01)  # Signatures that appear in > 1% of txs
        
        bytes_saved = common_signatures * 3  # 3 bytes saved per common signature transaction
        
        return {
            'bytes_saved_per_tx': bytes_saved / total_txs,
            'total_bytes_saved': bytes_saved,
            'percentage_savings': (bytes_saved / (total_txs * 4)) * 100 if total_txs > 0 else 0,
        }
    
    def analyze_parameter_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in function parameters"""
        # Analyze parameters for common function signatures
        param_patterns = {}
        
        # Group transactions by function signature
        signature_txs = defaultdict(list)
        
        for tx in self.transactions:
            input_data = tx.get('input', '')
            if not input_data or input_data == '0x' or len(input_data) < 10:
                continue
                
            signature = self._extract_function_signature(input_data)
            if signature:
                signature_txs[signature].append(input_data)
        
        # Analyze top signatures with enough samples
        for signature, tx_inputs in tqdm(signature_txs.items(), desc="Analyzing parameter patterns"):
            if len(tx_inputs) < 20:  # Skip signatures with too few samples
                continue
                
            # Analyze parameter positions for consistent values
            param_positions = self._analyze_parameter_positions(signature, tx_inputs)
            
            if param_positions:
                param_patterns[signature] = {
                    'decoded': self._decode_function_signature(signature),
                    'sample_count': len(tx_inputs),
                    'parameter_patterns': param_positions,
                }
        
        return {
            'total_signatures_analyzed': len(param_patterns),
            'parameter_patterns': param_patterns,
        }
    
    def _analyze_parameter_positions(self, signature: str, tx_inputs: List[str]) -> Dict[str, Any]:
        """Analyze parameter positions for consistent values or patterns"""
        # For simplicity, analyze in 32-byte chunks (typical EVM word size)
        chunk_size = 64  # 32 bytes = 64 hex chars
        
        # Skip the function signature (first 4 bytes / 8 hex chars + '0x')
        min_input_len = min(len(input_data) for input_data in tx_inputs)
        max_chunks = (min_input_len - 10) // chunk_size
        
        if max_chunks <= 0:
            return {}
            
        patterns = {}
        
        for chunk_idx in range(max_chunks):
            start_pos = 10 + chunk_idx * chunk_size
            end_pos = start_pos + chunk_size
            
            # Extract this chunk from all transactions
            chunks = [tx[start_pos:end_pos] for tx in tx_inputs]
            
            # Count values
            value_counts = Counter(chunks)
            
            # Check if there's a dominant value
            most_common_value, most_common_count = value_counts.most_common(1)[0]
            most_common_percentage = (most_common_count / len(chunks)) * 100
            
            # Check for zeros
            zero_value = '0' * chunk_size
            zero_count = value_counts.get(zero_value, 0)
            zero_percentage = (zero_count / len(chunks)) * 100
            
            # Check if addresses (20 bytes padded to 32)
            address_pattern = re.compile('^0{24}[a-fA-F0-9]{40}$')
            address_count = sum(1 for chunk in chunks if address_pattern.match(chunk))
            address_percentage = (address_count / len(chunks)) * 100
            
            # Store pattern information
            patterns[f'param_{chunk_idx+1}'] = {
                'position': f"bytes {chunk_idx*32+4}-{(chunk_idx+1)*32+4}",
                'unique_values': len(value_counts),
                'most_common_value': most_common_value,
                'most_common_percentage': most_common_percentage,
                'zero_percentage': zero_percentage,
                'address_percentage': address_percentage,
                'looks_like_address': address_percentage > 80,
                'looks_like_constant': most_common_percentage > 80,
                'looks_like_zeros': zero_percentage > 80,
                'entropy': self._calculate_entropy(value_counts, len(chunks)),
                'compressibility': max(0, 100 - self._calculate_entropy(value_counts, len(chunks)) * 100 / 8)
            }
        
        return patterns
    
    def _calculate_entropy(self, value_counts: Counter, total: int) -> float:
        """Calculate Shannon entropy (in bits) for a distribution"""
        entropy = 0.0
        for value, count in value_counts.items():
            p = count / total
            entropy -= p * np.log2(p)
        return entropy
    
    def analyze_calldata_structure(self) -> Dict[str, Any]:
        """Analyze overall calldata structure and patterns"""
        calldata_sizes = []
        
        # Counters for various patterns
        has_function_signature = 0
        empty_calldata = 0
        contains_address = 0
        contains_zeros = 0
        
        # Regular expression for detecting addresses (20 bytes)
        address_pattern = re.compile('0{24}[a-fA-F0-9]{40}')
        
        for tx in tqdm(self.transactions, desc="Analyzing calldata structure"):
            input_data = tx.get('input', '')
            
            if not input_data or input_data == '0x':
                empty_calldata += 1
                continue
                
            # Collect size statistics (in bytes)
            calldata_size = len(input_data) // 2 - 1  # Subtract '0x'
            calldata_sizes.append(calldata_size)
            
            # Check for function signature
            if len(input_data) >= 10:
                has_function_signature += 1
            
            # Check for addresses
            if address_pattern.search(input_data):
                contains_address += 1
            
            # Check for zero bytes (0000)
            if '0000' in input_data:
                contains_zeros += 1
        
        # Calculate size statistics
        total_txs = len(self.transactions)
        total_calldata_bytes = sum(calldata_sizes)
        
        return {
            'total_transactions': total_txs,
            'calldata_size_stats': {
                'mean': np.mean(calldata_sizes) if calldata_sizes else 0,
                'median': np.median(calldata_sizes) if calldata_sizes else 0,
                'min': min(calldata_sizes) if calldata_sizes else 0,
                'max': max(calldata_sizes) if calldata_sizes else 0,
                'std_dev': np.std(calldata_sizes) if calldata_sizes else 0,
                'total_bytes': total_calldata_bytes
            },
            'pattern_percentages': {
                'empty_calldata': (empty_calldata / total_txs) * 100 if total_txs > 0 else 0,
                'has_function_signature': (has_function_signature / total_txs) * 100 if total_txs > 0 else 0,
                'contains_address': (contains_address / total_txs) * 100 if total_txs > 0 else 0,
                'contains_zeros': (contains_zeros / total_txs) * 100 if total_txs > 0 else 0,
            },
            'compression_estimate': {
                'signature_encoding': 3 * has_function_signature,  # 3 bytes saved per tx with signature
                'address_encoding': 12 * contains_address,  # ~12 bytes saved per tx with address
                'potential_savings_bytes': 3 * has_function_signature + 12 * contains_address,
                'potential_savings_percentage': 
                    ((3 * has_function_signature + 12 * contains_address) / total_calldata_bytes) * 100 
                    if total_calldata_bytes > 0 else 0
            }
        }
    
    def analyze_repeated_patterns(self) -> Dict[str, Any]:
        """Analyze repeated patterns in calldata"""
        # Look for common patterns in calldata
        ngram_sizes = [8, 16, 32]  # Look for patterns of different sizes (in hex characters)
        ngram_results = {}
        
        for ngram_size in ngram_sizes:
            pattern_counts = Counter()
            total_ngrams = 0
            
            for tx in tqdm(self.transactions, desc=f"Analyzing {ngram_size}-char patterns"):
                input_data = tx.get('input', '')
                if not input_data or input_data == '0x' or len(input_data) < 10 + ngram_size:
                    continue
                    
                # Skip function signature
                data = input_data[10:]
                
                # Extract n-grams
                for i in range(0, len(data) - ngram_size + 1, 2):  # Step by 2 to align with bytes
                    ngram = data[i:i+ngram_size]
                    pattern_counts[ngram] += 1
                    total_ngrams += 1
            
            # Filter for common patterns
            common_patterns = {
                pattern: count for pattern, count in pattern_counts.items() 
                if count > 10 and pattern != '0' * ngram_size  # Exclude all zeros
            }
            
            # Calculate coverage of common patterns
            total_common_occurrences = sum(common_patterns.values())
            common_pattern_coverage = (total_common_occurrences / total_ngrams) * 100 if total_ngrams > 0 else 0
            
            ngram_results[str(ngram_size)] = {
                'total_ngrams_analyzed': total_ngrams,
                'unique_patterns': len(pattern_counts),
                'common_patterns_count': len(common_patterns),
                'common_pattern_coverage': common_pattern_coverage,
                'top_patterns': [
                    {'pattern': pattern, 'count': count, 'percentage': (count / total_ngrams) * 100}
                    for pattern, count in pattern_counts.most_common(20)
                    if count > 10
                ]
            }
        
        return {
            'ngram_analysis': ngram_results,
            'compression_potential': {
                'dictionary_based': max(
                    0, 
                    min(
                        40,  # Cap at 40%
                        sum(results.get('common_pattern_coverage', 0) for results in ngram_results.values()) / 3
                    )
                )
            }
        }
    
    def generate_visualizations(self, results: Dict[str, Any], output_prefix: str = None):
        """Generate visualizations of calldata patterns"""
        if not output_prefix:
            output_prefix = os.path.join(self.output_dir, 'calldata_analysis')
        
        # Create figures directory if it doesn't exist
        figures_dir = os.path.join(self.output_dir, 'figures')
        os.makedirs(figures_dir, exist_ok=True)
        
        # 1. Function signature distribution
        if 'top_signatures' in results.get('function_analysis', {}):
            top_signatures = results['function_analysis']['top_signatures']
            
            # Take top 15 signatures by count
            top_15 = {
                sig: data for sig, data in sorted(
                    top_signatures.items(), 
                    key=lambda x: x[1]['count'], 
                    reverse=True
                )[:15]
            }
            
            if top_15:
                plt.figure(figsize=(14, 7))
                
                labels = [f"{data['decoded'][:20]}" for sig, data in top_15.items()]
                counts = [data['count'] for sig, data in top_15.items()]
                
                plt.bar(labels, counts)
                plt.title('Top 15 Function Signatures by Transaction Count')
                plt.xlabel('Function Signature')
                plt.ylabel('Transaction Count')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(os.path.join(figures_dir, f'{output_prefix}_top_signatures.png'))
                plt.close()
        
        # 2. Calldata size distribution
        if 'calldata_structure' in results:
            struct_analysis = results['calldata_structure']
            calldata_sizes = [tx.get('input', '0x') for tx in self.transactions]
            calldata_sizes = [(len(data) // 2 - 1) for data in calldata_sizes if data and data != '0x']
            
            if calldata_sizes:
                plt.figure(figsize=(12, 6))
                
                # Plot histogram with logarithmic bins
                max_size = max(calldata_sizes)
                if max_size > 100:
                    bins = np.logspace(np.log10(4), np.log10(max_size), 50)
                    plt.hist(calldata_sizes, bins=bins)
                    plt.xscale('log')
                else:
                    plt.hist(calldata_sizes, bins=50)
                
                plt.title('Distribution of Calldata Sizes')
                plt.xlabel('Calldata Size (bytes)')
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(figures_dir, f'{output_prefix}_calldata_sizes.png'))
                plt.close()
        
        # 3. Pattern percentages
        if 'calldata_structure' in results and 'pattern_percentages' in results['calldata_structure']:
            pattern_percentages = results['calldata_structure']['pattern_percentages']
            
            plt.figure(figsize=(10, 6))
            
            labels = list(pattern_percentages.keys())
            values = list(pattern_percentages.values())
            
            plt.bar(labels, values)
            plt.title('Calldata Pattern Percentages')
            plt.xlabel('Pattern Type')
            plt.ylabel('Percentage of Transactions (%)')
            plt.ylim(0, 100)
            
            # Add value labels
            for i, v in enumerate(values):
                plt.text(i, v + 1, f"{v:.1f}%", ha='center')
                
            plt.tight_layout()
            plt.savefig(os.path.join(figures_dir, f'{output_prefix}_pattern_percentages.png'))
            plt.close()
        
        # 4. Compression potential summary
        if all(k in results for k in ['function_analysis', 'calldata_structure', 'repeated_patterns']):
            plt.figure(figsize=(10, 6))
            
            # Gather compression estimates from different analyses
            compression_methods = [
                'Function Signature Encoding',
                'Address Encoding',
                'Dictionary Compression',
                'Combined Approach'
            ]
            
            savings = [
                results['function_analysis']['compression_potential']['percentage_savings'],
                results['calldata_structure']['compression_estimate']['potential_savings_percentage'],
                results['repeated_patterns']['compression_potential']['dictionary_based'],
                min(95, sum([  # Combined approach, capped at 95%
                    results['function_analysis']['compression_potential']['percentage_savings'] * 0.9,
                    results['calldata_structure']['compression_estimate']['potential_savings_percentage'] * 0.9,
                    results['repeated_patterns']['compression_potential']['dictionary_based'] * 0.8
                ]))
            ]
            
            plt.bar(compression_methods, savings)
            plt.title('Potential Calldata Savings by Compression Method')
            plt.xlabel('Compression Method')
            plt.ylabel('Potential Savings (%)')
            plt.ylim(0, 100)
            
            # Add value labels
            for i, v in enumerate(savings):
                plt.text(i, v + 1, f"{v:.1f}%", ha='center')
                
            plt.tight_layout()
            plt.savefig(os.path.join(figures_dir, f'{output_prefix}_compression_potential.png'))
            plt.close()
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save analysis results to a file"""
        if not filename:
            filename = os.path.basename(self.input_file).replace('.json', '_calldata_analysis.json')
        
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved analysis to {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description='Analyze calldata patterns in transaction data')
    parser.add_argument('--input-file', type=str, required=True,
                       help='Path to JSON file containing transaction data')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Directory to save output files (default: same as input file directory)')
    parser.add_argument('--output-prefix', type=str, default=None,
                       help='Prefix for output filenames')
    
    args = parser.parse_args()
    
    try:
        analyzer = CalldataPatternAnalyzer(args.input_file, args.output_dir)
        
        # Analyze function signatures
        function_results = analyzer.analyze_function_signatures()
        logger.info(f"Function signature analysis: found {function_results['unique_signatures']} unique signatures")
        
        # Analyze parameter patterns
        parameter_results = analyzer.analyze_parameter_patterns()
        logger.info(f"Parameter pattern analysis: analyzed {parameter_results['total_signatures_analyzed']} signatures")
        
        # Analyze calldata structure
        structure_results = analyzer.analyze_calldata_structure()
        logger.info(f"Calldata structure analysis: analyzed {structure_results['total_transactions']} transactions")
        
        # Analyze repeated patterns
        pattern_results = analyzer.analyze_repeated_patterns()
        logger.info(f"Repeated pattern analysis: completed for multiple n-gram sizes")
        
        # Combine results
        results = {
            'function_analysis': function_results,
            'parameter_analysis': parameter_results,
            'calldata_structure': structure_results,
            'repeated_patterns': pattern_results,
        }
        
        # Save results
        analyzer.save_results(results)
        
        # Generate visualizations
        analyzer.generate_visualizations(results, args.output_prefix)
        
        logger.info("Calldata pattern analysis completed successfully")
    
    except Exception as e:
        logger.error(f"Error in calldata pattern analysis: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 