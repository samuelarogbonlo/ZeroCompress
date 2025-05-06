#!/usr/bin/env python3
"""
ZeroCompress Analysis Runner

This script orchestrates the running of data collection and analysis tools.
It can run each tool individually or in a complete pipeline.
"""

import os
import sys
import argparse
import logging
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Any

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

class AnalysisRunner:
    def __init__(self, output_dir: str = None, network: str = "arbitrum"):
        """Initialize the analysis runner"""
        # Default to current directory if no output dir specified
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "analysis_results")
        
        self.output_dir = output_dir
        self.network = network
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Path to the scripts
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        logger.info(f"Initialized analysis runner for network: {network}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def collect_transactions(self, block_count: int = 10, max_txs: int = 1000) -> str:
        """Run the transaction collector script"""
        output_file = os.path.join(self.output_dir, f"{self.network}_transactions.json")
        
        cmd = [
            sys.executable,
            os.path.join(self.script_dir, "transaction_collector.py"),
            "--network", self.network,
            "--blocks", str(block_count),
            "--max-transactions", str(max_txs),
            "--output-file", output_file
        ]
        
        logger.info(f"Running transaction collector for {self.network}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Transaction collection completed: {result.stdout}")
            return output_file
        except subprocess.CalledProcessError as e:
            logger.error(f"Transaction collection failed: {e.stderr}")
            raise
    
    def analyze_addresses(self, input_file: str) -> str:
        """Run the address pattern analyzer script"""
        output_dir = os.path.join(self.output_dir, "address_analysis")
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            sys.executable,
            os.path.join(self.script_dir, "address_pattern_analyzer.py"),
            "--input-file", input_file,
            "--output-dir", output_dir,
            "--output-prefix", self.network
        ]
        
        logger.info(f"Running address pattern analyzer on {input_file}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Address analysis completed: {result.stdout}")
            return output_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Address analysis failed: {e.stderr}")
            raise
    
    def analyze_zero_bytes(self, input_file: str) -> str:
        """Run the zero-byte pattern analyzer script"""
        output_dir = os.path.join(self.output_dir, "zero_byte_analysis")
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            sys.executable,
            os.path.join(self.script_dir, "zero_byte_analyzer.py"),
            "--input-file", input_file,
            "--output-dir", output_dir,
            "--output-prefix", self.network
        ]
        
        logger.info(f"Running zero-byte pattern analyzer on {input_file}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Zero-byte analysis completed: {result.stdout}")
            return output_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Zero-byte analysis failed: {e.stderr}")
            raise
    
    def analyze_calldata(self, input_file: str) -> str:
        """Run the calldata pattern analyzer script"""
        output_dir = os.path.join(self.output_dir, "calldata_analysis")
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            sys.executable,
            os.path.join(self.script_dir, "calldata_pattern_analyzer.py"),
            "--input-file", input_file,
            "--output-dir", output_dir,
            "--output-prefix", self.network
        ]
        
        logger.info(f"Running calldata pattern analyzer on {input_file}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Calldata analysis completed: {result.stdout}")
            return output_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Calldata analysis failed: {e.stderr}")
            raise
    
    def generate_summary_report(self, analysis_results: Dict[str, str]) -> str:
        """Generate a summary report of all analyses"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.output_dir, f"{self.network}_summary_report_{timestamp}.md")
        
        # Find all JSON result files
        result_files = {}
        for analysis_type, directory in analysis_results.items():
            json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
            if json_files:
                result_files[analysis_type] = os.path.join(directory, json_files[0])
        
        # Load results
        results = {}
        for analysis_type, file_path in result_files.items():
            try:
                with open(file_path, 'r') as f:
                    results[analysis_type] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {analysis_type} results: {e}")
        
        # Generate report
        with open(report_file, 'w') as f:
            f.write(f"# ZeroCompress Analysis Summary Report\n\n")
            f.write(f"Network: {self.network}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Address analysis summary
            if 'address' in results:
                address_results = results['address']
                f.write("## Address Analysis Summary\n\n")
                f.write(f"- Total addresses analyzed: {address_results.get('total_addresses', 'N/A')}\n")
                f.write(f"- Unique addresses: {address_results.get('unique_addresses', 'N/A')}\n")
                if 'frequent_addresses' in address_results:
                    f.write(f"- Top 5 most frequent addresses:\n")
                    for addr in address_results['frequent_addresses'][:5]:
                        f.write(f"  - {addr.get('address', 'N/A')}: {addr.get('count', 'N/A')} occurrences\n")
                f.write(f"- Estimated compression potential: {address_results.get('compression_potential', {}).get('overall_savings_percentage', 'N/A')}%\n\n")
            
            # Zero-byte analysis summary
            if 'zero_byte' in results:
                zero_results = results['zero_byte'].get('zero_byte_pattern_analysis', {})
                f.write("## Zero-Byte Analysis Summary\n\n")
                f.write(f"- Total bytes analyzed: {zero_results.get('total_bytes_analyzed', 'N/A')}\n")
                f.write(f"- Zero bytes percentage: {zero_results.get('zero_byte_percentage', 'N/A'):.2f}%\n")
                f.write(f"- Longest zero sequence: {zero_results.get('longest_zero_sequence', 'N/A')} bytes\n")
                
                compression = zero_results.get('compression_potential', {})
                f.write(f"- Compression potential:\n")
                f.write(f"  - Simple encoding: {compression.get('simple_encoding_savings_percentage', 'N/A'):.2f}%\n")
                f.write(f"  - RLE encoding: {compression.get('rle_encoding_savings_percentage', 'N/A'):.2f}%\n")
                f.write(f"  - Combined approach: {compression.get('combined_approach_savings_percentage', 'N/A'):.2f}%\n\n")
            
            # Calldata analysis summary
            if 'calldata' in results:
                calldata_results = results['calldata']
                f.write("## Calldata Analysis Summary\n\n")
                
                function_analysis = calldata_results.get('function_analysis', {})
                f.write(f"- Total transactions analyzed: {function_analysis.get('total_transactions_analyzed', 'N/A')}\n")
                f.write(f"- Unique function signatures: {function_analysis.get('unique_signatures', 'N/A')}\n")
                
                structure = calldata_results.get('calldata_structure', {})
                size_stats = structure.get('calldata_size_stats', {})
                f.write(f"- Calldata size statistics:\n")
                f.write(f"  - Mean: {size_stats.get('mean', 'N/A'):.2f} bytes\n")
                f.write(f"  - Median: {size_stats.get('median', 'N/A'):.2f} bytes\n")
                f.write(f"  - Max: {size_stats.get('max', 'N/A')} bytes\n")
                
                patterns = structure.get('pattern_percentages', {})
                f.write(f"- Pattern percentages:\n")
                f.write(f"  - Function signatures: {patterns.get('has_function_signature', 'N/A'):.2f}%\n")
                f.write(f"  - Contains addresses: {patterns.get('contains_address', 'N/A'):.2f}%\n")
                f.write(f"  - Contains zeros: {patterns.get('contains_zeros', 'N/A'):.2f}%\n")
                
                compression_estimate = structure.get('compression_estimate', {})
                f.write(f"- Estimated compression potential: {compression_estimate.get('potential_savings_percentage', 'N/A'):.2f}%\n\n")
            
            # Overall compression potential
            f.write("## Overall Compression Potential\n\n")
            
            address_savings = results.get('address', {}).get('compression_potential', {}).get('overall_savings_percentage', 0)
            zero_savings = results.get('zero_byte', {}).get('zero_byte_pattern_analysis', {}).get('compression_potential', {}).get('combined_approach_savings_percentage', 0)
            calldata_savings = results.get('calldata', {}).get('calldata_structure', {}).get('compression_estimate', {}).get('potential_savings_percentage', 0)
            
            # Simple weighted average (can be more sophisticated based on data volume)
            overall_potential = (address_savings * 0.3 + zero_savings * 0.4 + calldata_savings * 0.3)
            
            f.write(f"Based on the analysis of this dataset, the estimated overall compression potential is approximately **{overall_potential:.2f}%**.\n\n")
            f.write("This takes into account:\n")
            f.write(f"- Address compression: {address_savings:.2f}%\n")
            f.write(f"- Zero-byte elimination: {zero_savings:.2f}%\n")
            f.write(f"- Calldata structure optimization: {calldata_savings:.2f}%\n\n")
            
            f.write("## Next Steps\n\n")
            f.write("1. Implement compression techniques with highest potential savings\n")
            f.write("2. Develop benchmarking framework to validate compression ratios\n")
            f.write("3. Create prototype with client-side compression and on-chain decompression\n")
            
        logger.info(f"Generated summary report: {report_file}")
        return report_file
    
    def run_full_pipeline(self, block_count: int = 10, max_txs: int = 1000) -> str:
        """Run the complete analysis pipeline"""
        logger.info(f"Starting full analysis pipeline for {self.network}")
        
        try:
            # Step 1: Collect transactions
            transaction_file = self.collect_transactions(block_count, max_txs)
            
            # Step 2: Run all analyzers
            analysis_results = {
                'address': self.analyze_addresses(transaction_file),
                'zero_byte': self.analyze_zero_bytes(transaction_file),
                'calldata': self.analyze_calldata(transaction_file)
            }
            
            # Step 3: Generate summary report
            report_file = self.generate_summary_report(analysis_results)
            
            logger.info(f"Analysis pipeline completed successfully")
            logger.info(f"Summary report: {report_file}")
            
            return report_file
            
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
            raise

def main():
    parser = argparse.ArgumentParser(description='Run ZeroCompress data collection and analysis pipeline')
    
    parser.add_argument('--network', type=str, default='arbitrum',
                      choices=['arbitrum', 'optimism', 'base'],
                      help='Network to analyze (default: arbitrum)')
    
    parser.add_argument('--output-dir', type=str, default=None,
                      help='Directory to save output files')
    
    parser.add_argument('--blocks', type=int, default=10,
                      help='Number of blocks to collect (default: 10)')
    
    parser.add_argument('--max-txs', type=int, default=1000,
                      help='Maximum number of transactions to collect (default: 1000)')
    
    parser.add_argument('--mode', type=str, default='full',
                      choices=['full', 'collect', 'address', 'zero', 'calldata'],
                      help='Mode of operation (default: full)')
    
    parser.add_argument('--input-file', type=str,
                      help='Input transaction file (required for individual analysis modes)')
    
    args = parser.parse_args()
    
    try:
        runner = AnalysisRunner(args.output_dir, args.network)
        
        if args.mode == 'full':
            runner.run_full_pipeline(args.blocks, args.max_txs)
        
        elif args.mode == 'collect':
            transaction_file = runner.collect_transactions(args.blocks, args.max_txs)
            print(f"Transactions collected: {transaction_file}")
        
        else:
            if not args.input_file:
                parser.error("--input-file is required for individual analysis modes")
            
            if args.mode == 'address':
                output_dir = runner.analyze_addresses(args.input_file)
                print(f"Address analysis completed: {output_dir}")
            
            elif args.mode == 'zero':
                output_dir = runner.analyze_zero_bytes(args.input_file)
                print(f"Zero-byte analysis completed: {output_dir}")
            
            elif args.mode == 'calldata':
                output_dir = runner.analyze_calldata(args.input_file)
                print(f"Calldata analysis completed: {output_dir}")
    
    except Exception as e:
        logger.error(f"Error running analysis: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 