#!/usr/bin/env python3
"""
ZeroCompress Address Pattern Analyzer

This script analyzes address patterns in transaction data to evaluate the potential
effectiveness of address compression techniques.
"""

import os
import json
import argparse
import logging
from typing import Dict, List, Set, Any, Tuple
from collections import Counter, defaultdict

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("address_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AddressPatternAnalyzer:
    def __init__(self, input_file: str, output_dir: str = None):
        """Initialize the address pattern analyzer"""
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
    
    def analyze_address_frequency(self) -> Dict[str, Any]:
        """Analyze frequency of addresses in transactions"""
        # Extract 'to' and 'from' addresses
        to_addresses = [tx.get('to') for tx in self.transactions if tx.get('to')]
        from_addresses = [tx.get('from') for tx in self.transactions if tx.get('from')]
        
        # Count address occurrences
        to_counter = Counter(to_addresses)
        from_counter = Counter(from_addresses)
        
        # Combine counters
        all_addresses = to_addresses + from_addresses
        all_counter = Counter(all_addresses)
        
        # Get unique address counts
        unique_to = len(to_counter)
        unique_from = len(from_counter)
        unique_all = len(all_counter)
        
        # Calculate statistics
        frequency_stats = {
            'total_address_references': len(all_addresses),
            'unique_addresses': unique_all,
            'unique_to_addresses': unique_to,
            'unique_from_addresses': unique_from,
            'address_reuse_rate': (len(all_addresses) - unique_all) / len(all_addresses) if all_addresses else 0,
            'top_addresses': self._get_top_addresses(all_counter, 20),
            'address_frequency_distribution': self._get_frequency_distribution(all_counter),
        }
        
        # Calculate pointer size required
        if unique_all > 0:
            if unique_all <= 256:  # 2^8
                pointer_size = 1
            elif unique_all <= 65536:  # 2^16
                pointer_size = 2
            elif unique_all <= 16777216:  # 2^24
                pointer_size = 3
            else:
                pointer_size = 4
            
            # Calculate potential savings
            original_size = len(all_addresses) * 20  # 20 bytes per address
            compressed_size = unique_all * 20 + (len(all_addresses) - unique_all) * pointer_size
            savings = 1 - (compressed_size / original_size)
            
            frequency_stats.update({
                'pointer_size_bytes': pointer_size,
                'original_address_bytes': original_size,
                'compressed_address_bytes': compressed_size,
                'potential_savings_percentage': savings * 100,
            })
        
        return frequency_stats
    
    def _get_top_addresses(self, counter: Counter, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N most frequent addresses"""
        return [
            {'address': addr, 'count': count, 'percentage': count / sum(counter.values()) * 100}
            for addr, count in counter.most_common(n)
        ]
    
    def _get_frequency_distribution(self, counter: Counter) -> Dict[str, int]:
        """Get distribution of address frequencies"""
        frequency_bins = {
            '1': 0,         # Appeared once
            '2-5': 0,       # Appeared 2-5 times
            '6-10': 0,      # Appeared 6-10 times
            '11-50': 0,     # Appeared 11-50 times
            '51-100': 0,    # Appeared 51-100 times
            '101-500': 0,   # Appeared 101-500 times
            '501+': 0       # Appeared 501+ times
        }
        
        for _, count in counter.items():
            if count == 1:
                frequency_bins['1'] += 1
            elif 2 <= count <= 5:
                frequency_bins['2-5'] += 1
            elif 6 <= count <= 10:
                frequency_bins['6-10'] += 1
            elif 11 <= count <= 50:
                frequency_bins['11-50'] += 1
            elif 51 <= count <= 100:
                frequency_bins['51-100'] += 1
            elif 101 <= count <= 500:
                frequency_bins['101-500'] += 1
            else:
                frequency_bins['501+'] += 1
        
        return frequency_bins
    
    def analyze_address_patterns_in_calldata(self) -> Dict[str, Any]:
        """Analyze addresses embedded in transaction calldata"""
        embedded_addresses = []
        
        for tx in tqdm(self.transactions, desc="Analyzing calldata for addresses"):
            input_data = tx.get('input', '')
            if not input_data or input_data == '0x' or len(input_data) < 10:
                continue
            
            # Skip 0x and function selector (4 bytes)
            data = input_data[10:]
            
            # Check for potential addresses in calldata (20 bytes chunks aligned to 32 bytes)
            for i in range(0, len(data), 64):  # 32 bytes = 64 hex chars
                if i + 64 <= len(data):
                    # Extract potential address (last 20 bytes of 32 byte chunk)
                    potential_addr = '0x' + data[i+24:i+64].lower()
                    
                    # Simple heuristic: check if it looks like an address
                    # (non-zero, not all zeros or ones)
                    if potential_addr.startswith('0x') and \
                       potential_addr != '0x0000000000000000000000000000000000000000' and \
                       potential_addr != '0xffffffffffffffffffffffffffffffffffffffff':
                        embedded_addresses.append(potential_addr)
        
        # Analyze embedded addresses
        embedded_counter = Counter(embedded_addresses)
        unique_embedded = len(embedded_counter)
        
        calldata_stats = {
            'total_embedded_addresses': len(embedded_addresses),
            'unique_embedded_addresses': unique_embedded,
            'address_reuse_rate_in_calldata': (len(embedded_addresses) - unique_embedded) / len(embedded_addresses) if embedded_addresses else 0,
            'top_embedded_addresses': self._get_top_addresses(embedded_counter, 20),
            'embedded_address_frequency': self._get_frequency_distribution(embedded_counter),
        }
        
        # Calculate potential savings from compressing embedded addresses
        if embedded_addresses:
            original_size = len(embedded_addresses) * 20  # 20 bytes per address
            
            # Calculate pointer sizes
            if unique_embedded <= 256:  # 2^8
                pointer_size = 1
            elif unique_embedded <= 65536:  # 2^16
                pointer_size = 2
            elif unique_embedded <= 16777216:  # 2^24
                pointer_size = 3
            else:
                pointer_size = 4
            
            compressed_size = unique_embedded * 20 + (len(embedded_addresses) - unique_embedded) * pointer_size
            savings = 1 - (compressed_size / original_size)
            
            calldata_stats.update({
                'embedded_pointer_size_bytes': pointer_size,
                'original_embedded_bytes': original_size,
                'compressed_embedded_bytes': compressed_size,
                'potential_calldata_savings_percentage': savings * 100,
            })
        
        return calldata_stats
    
    def analyze_temporal_locality(self) -> Dict[str, Any]:
        """Analyze temporal locality of addresses"""
        # Sort transactions by timestamp
        sorted_txs = sorted(self.transactions, key=lambda x: x.get('timestamp', 0))
        
        # Create sliding windows to analyze address reuse in time windows
        window_sizes = [50, 100, 200, 500, 1000]
        results = {}
        
        for window_size in window_sizes:
            window_stats = []
            
            for i in range(0, len(sorted_txs), window_size//2):  # 50% overlap between windows
                window = sorted_txs[i:i+window_size]
                if len(window) < window_size // 2:  # Skip if window too small
                    continue
                
                # Extract addresses in this window
                window_to = [tx.get('to') for tx in window if tx.get('to')]
                window_from = [tx.get('from') for tx in window if tx.get('from')]
                window_all = window_to + window_from
                
                unique_addresses = len(set(window_all))
                
                window_stats.append({
                    'window_start': i,
                    'window_size': len(window),
                    'total_addresses': len(window_all),
                    'unique_addresses': unique_addresses,
                    'compression_ratio': len(window_all) / unique_addresses if unique_addresses else 0,
                })
            
            # Calculate average compression ratio across windows
            if window_stats:
                avg_compression_ratio = sum(w['compression_ratio'] for w in window_stats) / len(window_stats)
                max_compression_ratio = max(w['compression_ratio'] for w in window_stats)
                
                results[f'window_{window_size}'] = {
                    'window_count': len(window_stats),
                    'avg_compression_ratio': avg_compression_ratio,
                    'max_compression_ratio': max_compression_ratio,
                    'detailed_windows': window_stats[:10],  # First 10 windows for reference
                }
        
        return {
            'temporal_locality_analysis': results
        }
    
    def generate_visualizations(self, address_stats: Dict[str, Any], calldata_stats: Dict[str, Any], output_prefix: str = None):
        """Generate visualizations of address patterns"""
        if not output_prefix:
            output_prefix = os.path.join(self.output_dir, 'address_analysis')
        
        # Create figures directory if it doesn't exist
        figures_dir = os.path.join(self.output_dir, 'figures')
        os.makedirs(figures_dir, exist_ok=True)
        
        # Plot address frequency distribution
        if 'address_frequency_distribution' in address_stats:
            freq_dist = address_stats['address_frequency_distribution']
            plt.figure(figsize=(10, 6))
            plt.bar(freq_dist.keys(), freq_dist.values())
            plt.title('Distribution of Address Frequencies')
            plt.xlabel('Occurrence Frequency')
            plt.ylabel('Number of Addresses')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(figures_dir, f'{output_prefix}_freq_dist.png'))
            plt.close()
        
        # Plot top addresses
        if 'top_addresses' in address_stats:
            top_addresses = address_stats['top_addresses']
            
            if top_addresses:
                plt.figure(figsize=(12, 6))
                addresses = [f"{a['address'][:6]}...{a['address'][-4:]}" for a in top_addresses]
                counts = [a['count'] for a in top_addresses]
                
                plt.bar(addresses, counts)
                plt.title('Top Addresses by Frequency')
                plt.xlabel('Address')
                plt.ylabel('Occurrence Count')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(os.path.join(figures_dir, f'{output_prefix}_top_addresses.png'))
                plt.close()
        
        # Plot compression potential
        if all(k in address_stats for k in ['potential_savings_percentage', 'address_reuse_rate']):
            plt.figure(figsize=(8, 6))
            metrics = ['Address Reuse Rate', 'Potential Savings']
            values = [address_stats['address_reuse_rate'] * 100, address_stats['potential_savings_percentage']]
            
            plt.bar(metrics, values)
            plt.title('Address Compression Potential')
            plt.xlabel('Metric')
            plt.ylabel('Percentage (%)')
            plt.ylim(0, 100)
            
            # Add value labels
            for i, v in enumerate(values):
                plt.text(i, v + 1, f"{v:.1f}%", ha='center')
                
            plt.tight_layout()
            plt.savefig(os.path.join(figures_dir, f'{output_prefix}_compression_potential.png'))
            plt.close()
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save analysis results to a file"""
        if not filename:
            filename = os.path.basename(self.input_file).replace('.json', '_address_analysis.json')
        
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved analysis to {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description='Analyze address patterns in transaction data')
    parser.add_argument('--input-file', type=str, required=True,
                       help='Path to JSON file containing transaction data')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Directory to save output files (default: same as input file directory)')
    parser.add_argument('--output-prefix', type=str, default=None,
                       help='Prefix for output filenames')
    
    args = parser.parse_args()
    
    try:
        analyzer = AddressPatternAnalyzer(args.input_file, args.output_dir)
        
        # Analyze address frequency
        address_stats = analyzer.analyze_address_frequency()
        logger.info(f"Address analysis: {len(address_stats['top_addresses'])} top addresses identified")
        
        # Analyze calldata patterns
        calldata_stats = analyzer.analyze_address_patterns_in_calldata()
        logger.info(f"Calldata analysis: {calldata_stats.get('total_embedded_addresses', 0)} embedded addresses identified")
        
        # Analyze temporal locality
        temporal_stats = analyzer.analyze_temporal_locality()
        logger.info("Temporal locality analysis completed")
        
        # Combine results
        results = {
            'address_frequency_analysis': address_stats,
            'calldata_pattern_analysis': calldata_stats,
            'temporal_locality_analysis': temporal_stats,
        }
        
        # Save results
        analyzer.save_results(results)
        
        # Generate visualizations
        analyzer.generate_visualizations(address_stats, calldata_stats, args.output_prefix)
        
        logger.info("Address pattern analysis completed successfully")
    
    except Exception as e:
        logger.error(f"Error in address pattern analysis: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 