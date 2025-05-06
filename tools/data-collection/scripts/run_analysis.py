#!/usr/bin/env python3
"""
ZeroCompress Analysis Runner

This script runs all the analysis tools on a transaction dataset and prepares reports.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def prepare_data_for_analysis(input_file: str, output_file: str = None) -> str:
    """
    Prepare transaction data for analysis by ensuring it's in the correct format
    for our analysis tools.
    """
    if not output_file:
        input_name = os.path.basename(input_file)
        output_file = os.path.join(
            os.path.dirname(input_file),
            f"prepared_{input_name}"
        )
    
    logger.info(f"Preparing data from {input_file} for analysis")
    
    # Load the transaction data
    with open(input_file, 'r') as f:
        transactions = json.load(f)
    
    logger.info(f"Loaded {len(transactions)} transactions")
    
    # Standardize transaction format
    standardized_txs = []
    for tx in transactions:
        # Ensure required fields
        if 'input' not in tx:
            continue
        
        # Process input field - ensure hex string is properly formatted
        input_data = tx['input']
        if input_data.startswith('0x'):
            input_data = input_data[2:]
        
        # Create standardized transaction
        std_tx = {
            'from': tx.get('from', '0x0000000000000000000000000000000000000000'),
            'to': tx.get('to', '0x0000000000000000000000000000000000000000'),
            'input': input_data,  # Store without 0x prefix for analysis tools
            'type': tx.get('type', 'unknown'),
            'calldata_size': tx.get('calldata_size', len(input_data) // 2),
            'zero_bytes': tx.get('zero_bytes', 0),
            'zero_byte_percentage': tx.get('zero_byte_percentage', 0)
        }
        standardized_txs.append(std_tx)
    
    # Save prepared data
    with open(output_file, 'w') as f:
        json.dump(standardized_txs, f, indent=2)
    
    logger.info(f"Prepared data saved to {output_file}")
    return output_file

def run_zero_byte_analysis(input_file: str, output_dir: str, output_prefix: str = 'zero_byte') -> str:
    """Run zero-byte pattern analysis"""
    logger.info(f"Running zero-byte analysis on {input_file}")
    
    cmd = [
        sys.executable,
        "zero_byte_analyzer.py",
        "--input-file", input_file,
        "--output-dir", output_dir,
        "--output-prefix", output_prefix
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Zero-byte analysis completed successfully")
        return os.path.join(output_dir, f"{os.path.basename(input_file).replace('.json', '_zero_byte_analysis.json')}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Zero-byte analysis failed: {e}")
        return None

def run_address_analysis(input_file: str, output_dir: str, output_prefix: str = 'address') -> str:
    """Run address pattern analysis"""
    logger.info(f"Running address pattern analysis on {input_file}")
    
    cmd = [
        sys.executable,
        "address_pattern_analyzer.py",
        "--input-file", input_file,
        "--output-dir", output_dir,
        "--output-prefix", output_prefix
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Address pattern analysis completed successfully")
        return os.path.join(output_dir, f"{os.path.basename(input_file).replace('.json', '_address_analysis.json')}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Address pattern analysis failed: {e}")
        return None

def run_calldata_analysis(input_file: str, output_dir: str, output_prefix: str = 'calldata') -> str:
    """Run calldata pattern analysis"""
    logger.info(f"Running calldata pattern analysis on {input_file}")
    
    cmd = [
        sys.executable,
        "calldata_pattern_analyzer.py",
        "--input-file", input_file,
        "--output-dir", output_dir,
        "--output-prefix", output_prefix
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Calldata pattern analysis completed successfully")
        return os.path.join(output_dir, f"{os.path.basename(input_file).replace('.json', '_calldata_analysis.json')}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Calldata pattern analysis failed: {e}")
        return None

def generate_summary_report(analysis_files: Dict[str, str], output_file: str = None) -> str:
    """Generate a summary report from all analysis results"""
    logger.info(f"Generating summary report")
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"compression_summary_{timestamp}.json"
    
    # Load results from each analysis
    results = {}
    
    for analysis_type, file_path in analysis_files.items():
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                results[analysis_type] = json.load(f)
    
    # Extract key metrics for the summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'data_analyzed': {
            'transaction_count': results.get('zero_byte', {}).get('zero_byte_pattern_analysis', {}).get('transaction_count', 0),
            'total_bytes': results.get('zero_byte', {}).get('zero_byte_pattern_analysis', {}).get('total_bytes_analyzed', 0)
        },
        'compression_potential': {
            'zero_byte_compression': results.get('zero_byte', {}).get('zero_byte_pattern_analysis', {}).get('compression_potential', {}).get('combined_approach_savings_percentage', 0),
            'address_compression': results.get('address', {}).get('address_frequency_analysis', {}).get('potential_savings_percentage', 0),
            'calldata_pattern_compression': results.get('calldata', {}).get('calldata_pattern_analysis', {}).get('potential_savings', {}).get('combined_savings_percentage', 0)
        },
        'transaction_type_distribution': results.get('zero_byte', {}).get('transaction_type_analysis', {}).get('type_analysis', {})
    }
    
    # Calculate overall compression potential (combined techniques)
    zero_byte_compression = summary['compression_potential']['zero_byte_compression'] / 100 if summary['compression_potential']['zero_byte_compression'] else 0
    address_compression = summary['compression_potential']['address_compression'] / 100 if summary['compression_potential']['address_compression'] else 0
    calldata_compression = summary['compression_potential']['calldata_pattern_compression'] / 100 if summary['compression_potential']['calldata_pattern_compression'] else 0
    
    # Avoid double-counting by using a formula that considers overlapping techniques
    # 1 - (1-A)*(1-B)*(1-C) gives combined effect without double-counting
    overall_compression = 1 - (1 - zero_byte_compression) * (1 - address_compression) * (1 - calldata_compression)
    summary['compression_potential']['overall_compression_percentage'] = overall_compression * 100
    
    # Save summary report
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary report saved to {output_file}")
    logger.info(f"Overall compression potential: {overall_compression*100:.2f}%")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Run all ZeroCompress analysis tools on transaction data')
    parser.add_argument('--input-file', type=str, required=True,
                        help='Path to JSON file containing transaction data')
    parser.add_argument('--output-dir', type=str, default='./analysis',
                        help='Directory to save analysis output (default: ./analysis)')
    parser.add_argument('--summary-file', type=str, default=None,
                        help='Path to save summary report (default: auto-generated)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Prepare data for analysis
        prepared_file = prepare_data_for_analysis(args.input_file)
        
        # Run all analyses
        analysis_files = {}
        
        # Zero byte analysis
        analysis_files['zero_byte'] = run_zero_byte_analysis(
            prepared_file, 
            args.output_dir,
            'mock_zero_byte'
        )
        
        # Address pattern analysis
        analysis_files['address'] = run_address_analysis(
            prepared_file, 
            args.output_dir,
            'mock_address'
        )
        
        # Calldata pattern analysis
        analysis_files['calldata'] = run_calldata_analysis(
            prepared_file, 
            args.output_dir,
            'mock_calldata'
        )
        
        # Generate summary report
        summary_file = generate_summary_report(
            analysis_files,
            args.summary_file
        )
        
        logger.info(f"All analyses completed. Summary report: {summary_file}")
        
    except Exception as e:
        logger.error(f"Error running analyses: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 