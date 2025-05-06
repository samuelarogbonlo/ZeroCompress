#!/usr/bin/env python3
"""
ZeroCompress Zero-Byte Pattern Analyzer

This script analyzes zero-byte patterns in transaction data to evaluate the potential
effectiveness of zero-byte compression techniques.
"""

import os
import json
import argparse
import logging
from typing import Dict, List, Any, Tuple
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
        logging.FileHandler("zero_byte_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZeroByteAnalyzer:
    def __init__(self, input_file: str, output_dir: str = None):
        """Initialize the zero-byte pattern analyzer"""
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
    
    def _hex_to_bytes(self, hex_str: str) -> bytearray:
        """Convert hex string to bytearray"""
        # Handle empty or None input
        if not hex_str:
            return bytearray()
            
        # Remove 0x prefix if present
        if hex_str.startswith('0x'):
            hex_str = hex_str[2:]
        
        # Ensure even length
        if len(hex_str) % 2 != 0:
            hex_str = '0' + hex_str
        
        # Check for invalid characters and fix if needed
        try:
            return bytearray.fromhex(hex_str)
        except ValueError:
            # Clean the string by removing non-hex characters
            cleaned = ''.join(c for c in hex_str if c in '0123456789abcdefABCDEF')
            # Ensure even length again after cleaning
            if len(cleaned) % 2 != 0:
                cleaned = '0' + cleaned
                
            return bytearray.fromhex(cleaned)
    
    def analyze_zero_byte_patterns(self) -> Dict[str, Any]:
        """Analyze zero-byte patterns in transaction data"""
        # Statistics containers
        total_bytes = 0
        total_zero_bytes = 0
        zero_byte_sequences = []
        tx_zero_byte_percentages = []
        
        # Analyze each transaction
        for tx in tqdm(self.transactions, desc="Analyzing zero-byte patterns"):
            input_data = tx.get('input', '')
            if not input_data or input_data == '0x':
                continue
            
            # Convert to bytes
            data_bytes = self._hex_to_bytes(input_data)
            
            # Count zero bytes and sequences
            tx_zero_bytes = 0
            current_sequence = 0
            
            for byte in data_bytes:
                if byte == 0:
                    tx_zero_bytes += 1
                    current_sequence += 1
                else:
                    # Record sequence if it's at least 2 bytes long
                    if current_sequence >= 2:
                        zero_byte_sequences.append(current_sequence)
                    current_sequence = 0
            
            # Check if there's a sequence at the end
            if current_sequence >= 2:
                zero_byte_sequences.append(current_sequence)
            
            # Update totals
            total_bytes += len(data_bytes)
            total_zero_bytes += tx_zero_bytes
            
            # Calculate percentage for this transaction
            if len(data_bytes) > 0:
                tx_zero_byte_percentages.append(tx_zero_bytes / len(data_bytes) * 100)
        
        # Calculate overall statistics
        if total_bytes > 0:
            overall_zero_percentage = (total_zero_bytes / total_bytes) * 100
        else:
            overall_zero_percentage = 0
            
        # Analyze sequence distribution
        sequence_counts = Counter(zero_byte_sequences)
        
        # Calculate potential compression savings
        potential_savings = self._calculate_compression_savings(zero_byte_sequences, total_bytes, total_zero_bytes)
        
        return {
            'total_bytes_analyzed': total_bytes,
            'total_zero_bytes': total_zero_bytes,
            'zero_byte_percentage': overall_zero_percentage,
            'transaction_zero_byte_stats': {
                'mean_percentage': np.mean(tx_zero_byte_percentages) if tx_zero_byte_percentages else 0,
                'median_percentage': np.median(tx_zero_byte_percentages) if tx_zero_byte_percentages else 0,
                'min_percentage': min(tx_zero_byte_percentages) if tx_zero_byte_percentages else 0,
                'max_percentage': max(tx_zero_byte_percentages) if tx_zero_byte_percentages else 0,
                'std_dev': np.std(tx_zero_byte_percentages) if tx_zero_byte_percentages else 0,
            },
            'zero_byte_sequence_counts': {str(k): v for k, v in sorted(sequence_counts.items())},
            'longest_zero_sequence': max(zero_byte_sequences) if zero_byte_sequences else 0,
            'total_sequences': len(zero_byte_sequences),
            'compression_potential': potential_savings,
        }
    
    def _calculate_compression_savings(self, zero_sequences: List[int], total_bytes: int, total_zero_bytes: int) -> Dict[str, Any]:
        """Calculate potential compression savings using different approaches"""
        if not zero_sequences or total_bytes == 0:
            return {
                'simple_encoding_savings_percentage': 0,
                'rle_encoding_savings_percentage': 0,
                'combined_approach_savings_percentage': 0,
            }
        
        # 1. Simple replacement encoding (replace sequences with [0x00, length])
        # Replaces sequences of zeros with two bytes
        simple_encoding_bytes_saved = sum(seq - 2 for seq in zero_sequences if seq >= 3)
        simple_encoding_savings = (simple_encoding_bytes_saved / total_bytes) * 100
        
        # 2. Run-length encoding for zero bytes
        # Each sequence becomes [special_marker, length] (2 bytes)
        rle_encoding_bytes_saved = sum(seq - 2 for seq in zero_sequences if seq >= 3)
        rle_encoding_savings = (rle_encoding_bytes_saved / total_bytes) * 100
        
        # 3. Combined approach (theoretical best)
        # Assumes optimal compression of zero bytes and related patterns
        combined_approach_savings = min(95, (total_zero_bytes / total_bytes) * 80)  # 80% of zero bytes, max 95% total
        
        return {
            'simple_encoding_savings_percentage': simple_encoding_savings,
            'rle_encoding_savings_percentage': rle_encoding_savings,
            'combined_approach_savings_percentage': combined_approach_savings,
            'simple_encoding_bytes_saved': simple_encoding_bytes_saved,
            'total_zero_sequences': len(zero_sequences),
        }
    
    def analyze_transaction_types(self) -> Dict[str, Any]:
        """Analyze zero-byte patterns by transaction type"""
        # Group transactions by type
        transaction_types = defaultdict(list)
        
        for tx in self.transactions:
            tx_type = tx.get('type', 'unknown')
            transaction_types[tx_type].append(tx)
        
        # Analyze each type
        type_results = {}
        
        for tx_type, txs in transaction_types.items():
            if not txs:
                continue
                
            # Calculate zero-byte statistics for this type
            total_bytes = 0
            total_zero_bytes = 0
            
            for tx in txs:
                input_data = tx.get('input', '')
                if not input_data or input_data == '0x':
                    continue
                
                data_bytes = self._hex_to_bytes(input_data)
                
                # Count zero bytes
                zero_count = sum(1 for byte in data_bytes if byte == 0)
                
                total_bytes += len(data_bytes)
                total_zero_bytes += zero_count
            
            if total_bytes > 0:
                zero_percentage = (total_zero_bytes / total_bytes) * 100
            else:
                zero_percentage = 0
                
            # Store results
            type_results[tx_type] = {
                'transaction_count': len(txs),
                'total_bytes': total_bytes,
                'total_zero_bytes': total_zero_bytes,
                'zero_byte_percentage': zero_percentage,
                'potential_savings': zero_percentage * 0.7,  # Estimate: 70% of zero bytes can be compressed
            }
        
        return {
            'type_analysis': type_results,
            'total_types': len(type_results),
        }
    
    def analyze_byte_value_distribution(self) -> Dict[str, Any]:
        """Analyze distribution of all byte values in transaction data"""
        byte_value_counts = Counter()
        
        for tx in tqdm(self.transactions, desc="Analyzing byte value distribution"):
            input_data = tx.get('input', '')
            if not input_data or input_data == '0x':
                continue
            
            data_bytes = self._hex_to_bytes(input_data)
            byte_value_counts.update(data_bytes)
        
        total_bytes = sum(byte_value_counts.values())
        
        # Convert to percentage distribution
        distribution = {}
        for byte_value, count in sorted(byte_value_counts.items()):
            percentage = (count / total_bytes) * 100 if total_bytes > 0 else 0
            distribution[str(byte_value)] = {
                'count': count,
                'percentage': percentage,
            }
        
        # Calculate entropy (measure of randomness/compressibility)
        entropy = 0
        for byte_value, count in byte_value_counts.items():
            p = count / total_bytes if total_bytes > 0 else 0
            if p > 0:
                entropy -= p * np.log2(p)
        
        return {
            'byte_value_distribution': distribution,
            'most_common_bytes': [{'value': str(byte), 'count': count} 
                                 for byte, count in byte_value_counts.most_common(10)],
            'unique_byte_values': len(byte_value_counts),
            'entropy': entropy,
            'theoretical_compression_potential': max(0, (8 - entropy) / 8 * 100),  # 0-100% based on entropy
        }
    
    def generate_visualizations(self, results: Dict[str, Any], output_prefix: str = None):
        """Generate visualizations of zero-byte patterns"""
        if not output_prefix:
            output_prefix = os.path.join(self.output_dir, 'zero_byte_analysis')
        
        # Create figures directory if it doesn't exist
        figures_dir = os.path.join(self.output_dir, 'figures')
        os.makedirs(figures_dir, exist_ok=True)
        
        # 1. Zero-byte sequence length distribution
        if 'zero_byte_sequence_counts' in results:
            sequence_counts = results['zero_byte_sequence_counts']
            if sequence_counts:
                plt.figure(figsize=(12, 6))
                
                # Convert keys to integers and sort
                keys = sorted([int(k) for k in sequence_counts.keys()])
                values = [sequence_counts[str(k)] for k in keys]
                
                plt.bar(keys, values)
                plt.title('Distribution of Zero-Byte Sequence Lengths')
                plt.xlabel('Sequence Length (bytes)')
                plt.ylabel('Frequency')
                plt.yscale('log')  # Log scale for better visualization
                plt.tight_layout()
                plt.savefig(os.path.join(figures_dir, f'{output_prefix}_sequence_dist.png'))
                plt.close()
        
        # 2. Compression potential by transaction type
        if 'type_analysis' in results:
            type_analysis = results.get('type_analysis', {})
            if type_analysis:
                plt.figure(figsize=(14, 7))
                
                # Select top types by transaction count for clarity
                top_types = sorted(
                    type_analysis.items(), 
                    key=lambda x: x[1].get('transaction_count', 0), 
                    reverse=True
                )[:10]
                
                types = [t[0] for t in top_types]
                zero_percentages = [t[1].get('zero_byte_percentage', 0) for t in top_types]
                
                plt.bar(types, zero_percentages)
                plt.title('Zero-Byte Percentage by Transaction Type')
                plt.xlabel('Transaction Type')
                plt.ylabel('Zero-Byte Percentage (%)')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(os.path.join(figures_dir, f'{output_prefix}_type_analysis.png'))
                plt.close()
        
        # 3. Byte value distribution (top values)
        if 'most_common_bytes' in results:
            most_common = results['most_common_bytes']
            if most_common:
                plt.figure(figsize=(10, 6))
                
                labels = [f"0x{int(item['value']):02x}" for item in most_common]
                values = [item['count'] for item in most_common]
                
                plt.bar(labels, values)
                plt.title('Most Common Byte Values')
                plt.xlabel('Byte Value (hex)')
                plt.ylabel('Frequency')
                plt.tight_layout()
                plt.savefig(os.path.join(figures_dir, f'{output_prefix}_byte_distribution.png'))
                plt.close()
        
        # 4. Compression potential summary
        if 'compression_potential' in results:
            compression = results['compression_potential']
            
            plt.figure(figsize=(10, 6))
            methods = ['Simple Encoding', 'RLE Encoding', 'Combined Approach']
            savings = [
                compression.get('simple_encoding_savings_percentage', 0),
                compression.get('rle_encoding_savings_percentage', 0),
                compression.get('combined_approach_savings_percentage', 0)
            ]
            
            plt.bar(methods, savings)
            plt.title('Potential Storage Savings by Compression Method')
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
            filename = os.path.basename(self.input_file).replace('.json', '_zero_byte_analysis.json')
        
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved analysis to {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description='Analyze zero-byte patterns in transaction data')
    parser.add_argument('--input-file', type=str, required=True,
                       help='Path to JSON file containing transaction data')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Directory to save output files (default: same as input file directory)')
    parser.add_argument('--output-prefix', type=str, default=None,
                       help='Prefix for output filenames')
    
    args = parser.parse_args()
    
    try:
        analyzer = ZeroByteAnalyzer(args.input_file, args.output_dir)
        
        # Analyze zero-byte patterns
        pattern_results = analyzer.analyze_zero_byte_patterns()
        logger.info(f"Zero-byte analysis: {pattern_results['zero_byte_percentage']:.2f}% of bytes are zeros")
        
        # Analyze transaction types
        type_results = analyzer.analyze_transaction_types()
        logger.info(f"Type analysis: analyzed {type_results['total_types']} transaction types")
        
        # Analyze byte value distribution
        distribution_results = analyzer.analyze_byte_value_distribution()
        logger.info(f"Byte distribution analysis: {distribution_results['unique_byte_values']} unique byte values found")
        
        # Combine results
        results = {
            'zero_byte_pattern_analysis': pattern_results,
            'transaction_type_analysis': type_results,
            'byte_distribution_analysis': distribution_results,
        }
        
        # Save results
        analyzer.save_results(results)
        
        # Generate visualizations
        analyzer.generate_visualizations(results, args.output_prefix)
        
        logger.info("Zero-byte pattern analysis completed successfully")
    
    except Exception as e:
        logger.error(f"Error in zero-byte pattern analysis: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 