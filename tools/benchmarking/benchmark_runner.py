#!/usr/bin/env python3
"""
ZeroCompress Benchmarking Framework

This script provides a comprehensive framework for benchmarking different compression
techniques against standardized datasets, with a focus on comparing ZeroCompress
against other implementations like Sequence.xyz's CZIP.

The benchmark measures:
1. Compression ratio
2. Encoding time
3. Decoding time
4. Estimated gas costs for on-chain decompression
"""

import os
import json
import time
import argparse
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import sys

# Add the parent directory to the path so we can import the compression modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

# Import ZeroCompress modules
try:
    # Import directly from the modules
    from src.compression import zero_compressor
    from src.compression import address_compressor
    from src.compression import zero_byte_compressor
    from src.compression import function_selector_compressor
    from src.compression import calldata_compressor
    
    # Create classes
    ZeroCompressor = zero_compressor.ZeroCompressor
    AddressCompressor = address_compressor.AddressCompressor
    ZeroByteCompressor = zero_byte_compressor.ZeroByteCompressor
    FunctionSelectorCompressor = function_selector_compressor.FunctionSelectorCompressor
    CalldataCompressor = calldata_compressor.CalldataCompressor
except ImportError as e:
    logging.error(f"Failed to import ZeroCompress modules: {e}")
    logging.error("Make sure you're running this script from the root directory")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "benchmark.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ZeroCompress-Benchmark")

class CompressionBenchmark:
    """Benchmark framework for compression algorithms"""
    
    def __init__(self, config_path: str, output_dir: str = None):
        """
        Initialize the benchmark framework
        
        Args:
            config_path: Path to the benchmark configuration file
            output_dir: Directory to save benchmark results (default: results/YYYY-MM-DD_HH-MM-SS)
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_dir = os.path.join(os.path.dirname(__file__), "results", timestamp)
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Dictionary to store compressor implementations
        self.compressors = {}
        
        # Load dataset paths
        self.datasets = self._load_datasets()
        
        # Results storage
        self.results = {
            "summary": {},
            "detailed": {},
            "by_txn_type": {},
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load benchmark configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _load_datasets(self) -> Dict[str, str]:
        """Load datasets specified in the configuration"""
        datasets = {}
        for dataset_name, dataset_path in self.config.get("datasets", {}).items():
            # If it's an absolute path, use it directly
            if os.path.isabs(dataset_path):
                if os.path.exists(dataset_path):
                    datasets[dataset_name] = dataset_path
                    logger.info(f"Found dataset at {dataset_path}")
                else:
                    logger.warning(f"Dataset not found: {dataset_path}")
            else:
                # Relative path - join with the directory of the benchmark
                full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), dataset_path)
                if os.path.exists(full_path):
                    datasets[dataset_name] = full_path
                    logger.info(f"Found dataset at {full_path}")
                else:
                    logger.warning(f"Dataset not found: {full_path}")
        
        if not datasets:
            logger.error("No valid datasets found in configuration")
            raise ValueError("No valid datasets found")
        
        logger.info(f"Loaded {len(datasets)} datasets: {', '.join(datasets.keys())}")
        return datasets
    
    def register_compressor(self, name: str, compressor: Any) -> None:
        """
        Register a compressor implementation for benchmarking
        
        Args:
            name: Name of the compressor (e.g., "ZeroCompress", "Sequence-CZIP")
            compressor: Instance of a compressor class with compress and decompress methods
        """
        if hasattr(compressor, 'compress') and hasattr(compressor, 'decompress'):
            self.compressors[name] = compressor
            logger.info(f"Registered compressor: {name}")
        else:
            logger.error(f"Invalid compressor {name}: Missing compress or decompress method")
            raise ValueError(f"Invalid compressor {name}")
    
    def load_standard_compressors(self) -> None:
        """Load standard compressor implementations defined in the config"""
        # Load ZeroCompress
        self.register_compressor("ZeroCompress", ZeroCompressor())
        
        # Load individual ZeroCompress components for comparison
        self.register_compressor("ZeroByteCompressor", ZeroByteCompressor())
        self.register_compressor("AddressCompressor", AddressCompressor())
        self.register_compressor("FunctionSelectorCompressor", FunctionSelectorCompressor())
        self.register_compressor("CalldataCompressor", CalldataCompressor())
        
        # Load Sequence-style implementation
        sequence_impl_path = os.path.join(
            os.path.dirname(__file__), 
            "implementations", 
            "sequence_implementation.py"
        )
        
        if os.path.exists(sequence_impl_path):
            sys.path.append(os.path.dirname(sequence_impl_path))
            try:
                from sequence_implementation import SequenceCompressor
                self.register_compressor("Sequence-CZIP", SequenceCompressor())
            except ImportError:
                logger.warning("Could not import Sequence-CZIP implementation")
        else:
            logger.warning(f"Sequence implementation not found at {sequence_impl_path}")
    
    def run_benchmarks(self) -> None:
        """Run benchmarks for all registered compressors against all datasets"""
        logger.info("Starting benchmark runs")
        
        for dataset_name, dataset_path in self.datasets.items():
            logger.info(f"Processing dataset: {dataset_name}")
            
            # Load transaction data
            transactions = self._load_transaction_data(dataset_path)
            if not transactions:
                logger.error(f"No transactions found in dataset {dataset_name}")
                continue
            
            # Initialize results storage for this dataset
            self.results["detailed"][dataset_name] = {}
            
            # Process each compressor
            for compressor_name, compressor in self.compressors.items():
                logger.info(f"Benchmarking {compressor_name} on {dataset_name}")
                
                dataset_results = self._benchmark_compressor(
                    compressor_name, 
                    compressor, 
                    transactions,
                    dataset_name
                )
                
                self.results["detailed"][dataset_name][compressor_name] = dataset_results
            
            # Calculate comparative metrics
            self._calculate_comparative_metrics(dataset_name)
        
        # Generate summary results
        self._generate_summary()
        
        # Save results
        self._save_results()
        
        # Generate visualizations
        self._generate_visualizations()
        
        logger.info("Benchmark runs completed")
    
    def _load_transaction_data(self, dataset_path: str) -> List[Dict[str, Any]]:
        """Load transaction data from the specified dataset file"""
        try:
            with open(dataset_path, 'r') as f:
                data = json.load(f)
            
            # Handle different dataset formats
            if isinstance(data, list):
                transactions = data
            elif isinstance(data, dict) and "transactions" in data:
                transactions = data["transactions"]
            else:
                logger.error(f"Unknown dataset format in {dataset_path}")
                return []
            
            logger.info(f"Loaded {len(transactions)} transactions from {dataset_path}")
            return transactions
        
        except Exception as e:
            logger.error(f"Failed to load transaction data from {dataset_path}: {e}")
            return []
    
    def _benchmark_compressor(
        self, 
        compressor_name: str, 
        compressor: Any, 
        transactions: List[Dict[str, Any]],
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Benchmark a single compressor against a dataset of transactions
        
        Returns:
            Dictionary of benchmark results
        """
        results = {
            "compression_ratio": [],
            "compressed_size": [],
            "original_size": [],
            "encode_time": [],
            "decode_time": [],
            "estimated_gas": [],
            "transaction_type": [],
        }
        
        # Group by transaction type if available
        txn_type_results = {}
        
        for tx in tqdm(transactions, desc=f"Benchmarking {compressor_name}"):
            # Extract transaction data
            tx_data = tx.get("data", tx.get("input", "0x"))
            if tx_data.startswith("0x"):
                tx_data = tx_data[2:]  # Remove 0x prefix
            
            # Skip empty transactions
            if not tx_data:
                continue
            
            # Determine transaction type
            tx_type = self._determine_transaction_type(tx)
            results["transaction_type"].append(tx_type)
            
            # Prepare transaction-type specific results
            if tx_type not in txn_type_results:
                txn_type_results[tx_type] = {
                    "compression_ratio": [],
                    "compressed_size": [],
                    "original_size": [],
                    "encode_time": [],
                    "decode_time": [],
                    "estimated_gas": [],
                    "count": 0,
                }
            
            # Convert hex to bytes
            try:
                original_data = bytes.fromhex(tx_data)
            except ValueError:
                logger.warning(f"Invalid hex data in transaction: {tx_data[:30]}...")
                continue
                
            original_size = len(original_data)
            results["original_size"].append(original_size)
            txn_type_results[tx_type]["original_size"].append(original_size)
            
            # Measure compression time
            start_time = time.time()
            try:
                compressed_data = compressor.compress(original_data)
                compression_time = time.time() - start_time
                
                # Measure decompression time
                start_time = time.time()
                decompressed_data = compressor.decompress(compressed_data)
                decompression_time = time.time() - start_time
                
                # Verify correctness
                if decompressed_data != original_data:
                    logger.warning(
                        f"Decompression failed to match original data for {compressor_name} on transaction type {tx_type}"
                    )
                    continue
                
                # Calculate metrics
                compressed_size = len(compressed_data)
                compression_ratio = 1 - (compressed_size / original_size) if original_size > 0 else 0
                
                # Estimate gas costs (simplified model)
                estimated_gas = self._estimate_gas_cost(compressed_data, compressor_name)
                
                # Store results
                results["compressed_size"].append(compressed_size)
                results["compression_ratio"].append(compression_ratio)
                results["encode_time"].append(compression_time)
                results["decode_time"].append(decompression_time)
                results["estimated_gas"].append(estimated_gas)
                
                # Store transaction-type specific results
                txn_type_results[tx_type]["compressed_size"].append(compressed_size)
                txn_type_results[tx_type]["compression_ratio"].append(compression_ratio)
                txn_type_results[tx_type]["encode_time"].append(compression_time)
                txn_type_results[tx_type]["decode_time"].append(decompression_time)
                txn_type_results[tx_type]["estimated_gas"].append(estimated_gas)
                txn_type_results[tx_type]["count"] += 1
                
            except Exception as e:
                logger.error(f"Error benchmarking {compressor_name} on transaction: {e}")
                continue
        
        # Calculate aggregated results
        agg_results = {
            "avg_compression_ratio": np.mean(results["compression_ratio"]) if results["compression_ratio"] else 0,
            "median_compression_ratio": np.median(results["compression_ratio"]) if results["compression_ratio"] else 0,
            "min_compression_ratio": np.min(results["compression_ratio"]) if results["compression_ratio"] else 0,
            "max_compression_ratio": np.max(results["compression_ratio"]) if results["compression_ratio"] else 0,
            "avg_encode_time_ms": np.mean(results["encode_time"]) * 1000 if results["encode_time"] else 0,
            "avg_decode_time_ms": np.mean(results["decode_time"]) * 1000 if results["decode_time"] else 0,
            "avg_estimated_gas": np.mean(results["estimated_gas"]) if results["estimated_gas"] else 0,
            "total_transactions": len(results["compression_ratio"]),
            "by_transaction_type": {},
        }
        
        # Process transaction-type specific results
        for tx_type, tx_results in txn_type_results.items():
            if tx_results["count"] > 0:
                agg_results["by_transaction_type"][tx_type] = {
                    "avg_compression_ratio": np.mean(tx_results["compression_ratio"]),
                    "median_compression_ratio": np.median(tx_results["compression_ratio"]),
                    "avg_encode_time_ms": np.mean(tx_results["encode_time"]) * 1000,
                    "avg_decode_time_ms": np.mean(tx_results["decode_time"]) * 1000,
                    "avg_estimated_gas": np.mean(tx_results["estimated_gas"]),
                    "transaction_count": tx_results["count"],
                }
        
        # Store transaction-type specific results in global results
        if dataset_name not in self.results["by_txn_type"]:
            self.results["by_txn_type"][dataset_name] = {}
        
        self.results["by_txn_type"][dataset_name][compressor_name] = agg_results["by_transaction_type"]
        
        logger.info(
            f"Results for {compressor_name} on {dataset_name}: "
            f"Avg compression ratio: {agg_results['avg_compression_ratio']:.4f}, "
            f"Encode time: {agg_results['avg_encode_time_ms']:.2f}ms, "
            f"Decode time: {agg_results['avg_decode_time_ms']:.2f}ms, "
            f"Est. gas: {agg_results['avg_estimated_gas']:.0f}"
        )
        
        return agg_results
    
    def _determine_transaction_type(self, tx: Dict[str, Any]) -> str:
        """Determine the type of transaction based on its data or known type"""
        # Use predefined type if available
        if "type" in tx:
            return tx["type"]
        
        # Extract transaction data
        tx_data = tx.get("data", tx.get("input", "0x"))
        if tx_data == "0x" or not tx_data:
            return "simple_transfer"
        
        # Check for contract creation
        if "to" not in tx or tx["to"] is None or tx["to"] == "0x" or tx["to"] == "":
            return "contract_creation"
        
        # Check for function signature
        if len(tx_data) >= 10:  # At least function selector (0x + 8 chars)
            selector = tx_data[0:10]  # 0x + 4 bytes
            
            # Common ERC20 functions
            if selector == "0xa9059cbb":
                return "erc20_transfer"
            elif selector == "0x23b872dd":
                return "erc20_transferFrom"
            elif selector == "0x095ea7b3":
                return "erc20_approve"
            
            # Uniswap related
            if selector in ["0x7ff36ab5", "0xfb3bdb41", "0x38ed1739"]:
                return "uniswap_swap"
        
        # Default to generic contract interaction
        return "contract_interaction"
    
    def _estimate_gas_cost(self, compressed_data: bytes, compressor_name: str) -> int:
        """
        Estimate gas cost for decompressing data on-chain
        
        This is a simplified model based on data size and compressor complexity
        For actual gas costs, we would need to benchmark the Solidity implementation
        """
        # Base gas cost per bytes of compressed data
        base_cost = len(compressed_data) * 16  # 16 gas per byte is standard calldata cost
        
        # Additional cost based on compressor complexity
        if compressor_name == "ZeroCompress":
            # ZeroCompress uses multiple techniques, so estimated higher overhead
            overhead = len(compressed_data) * 5
        elif compressor_name == "ZeroByteCompressor":
            # Simpler processing overhead
            overhead = len(compressed_data) * 2
        elif compressor_name == "AddressCompressor":
            # Dictionary lookups add overhead
            overhead = len(compressed_data) * 3
        elif compressor_name == "Sequence-CZIP":
            # Based on published Sequence gas costs (if available)
            overhead = len(compressed_data) * 4
        else:
            # Default overhead
            overhead = len(compressed_data) * 3
        
        return base_cost + overhead
    
    def _calculate_comparative_metrics(self, dataset_name: str) -> None:
        """Calculate comparative metrics between different compressors"""
        compressors = list(self.results["detailed"][dataset_name].keys())
        if len(compressors) <= 1:
            return
        
        # For now, we'll use ZeroCompress as the baseline if available
        baseline = "ZeroCompress" if "ZeroCompress" in compressors else compressors[0]
        
        for compressor in compressors:
            if compressor == baseline:
                continue
            
            baseline_results = self.results["detailed"][dataset_name][baseline]
            compressor_results = self.results["detailed"][dataset_name][compressor]
            
            # Skip if no transactions were processed
            if baseline_results["total_transactions"] == 0 or compressor_results["total_transactions"] == 0:
                continue
            
            # Calculate relative metrics
            compression_ratio_diff = (
                compressor_results["avg_compression_ratio"] - baseline_results["avg_compression_ratio"]
            )
            
            encode_time_ratio = (
                compressor_results["avg_encode_time_ms"] / baseline_results["avg_encode_time_ms"]
                if baseline_results["avg_encode_time_ms"] > 0 else float('inf')
            )
            
            decode_time_ratio = (
                compressor_results["avg_decode_time_ms"] / baseline_results["avg_decode_time_ms"]
                if baseline_results["avg_decode_time_ms"] > 0 else float('inf')
            )
            
            gas_cost_ratio = (
                compressor_results["avg_estimated_gas"] / baseline_results["avg_estimated_gas"]
                if baseline_results["avg_estimated_gas"] > 0 else float('inf')
            )
            
            # Store comparative metrics
            if "comparative" not in self.results["detailed"][dataset_name]:
                self.results["detailed"][dataset_name]["comparative"] = {}
            
            self.results["detailed"][dataset_name]["comparative"][compressor] = {
                "baseline": baseline,
                "compression_ratio_diff": compression_ratio_diff,
                "encode_time_ratio": encode_time_ratio,
                "decode_time_ratio": decode_time_ratio,
                "gas_cost_ratio": gas_cost_ratio,
            }
            
            logger.info(
                f"Comparison {compressor} vs {baseline} on {dataset_name}: "
                f"Compression diff: {compression_ratio_diff:.4f}, "
                f"Encode time ratio: {encode_time_ratio:.2f}x, "
                f"Decode time ratio: {decode_time_ratio:.2f}x, "
                f"Gas cost ratio: {gas_cost_ratio:.2f}x"
            )
    
    def _generate_summary(self) -> None:
        """Generate summary results across all datasets"""
        # Calculate average metrics across all datasets for each compressor
        compressor_summary = {}
        
        for dataset_name, dataset_results in self.results["detailed"].items():
            for compressor_name, results in dataset_results.items():
                if compressor_name == "comparative":
                    continue
                
                if compressor_name not in compressor_summary:
                    compressor_summary[compressor_name] = {
                        "avg_compression_ratio": [],
                        "avg_encode_time_ms": [],
                        "avg_decode_time_ms": [],
                        "avg_estimated_gas": [],
                        "total_transactions": 0,
                    }
                
                compressor_summary[compressor_name]["avg_compression_ratio"].append(
                    results["avg_compression_ratio"]
                )
                compressor_summary[compressor_name]["avg_encode_time_ms"].append(
                    results["avg_encode_time_ms"]
                )
                compressor_summary[compressor_name]["avg_decode_time_ms"].append(
                    results["avg_decode_time_ms"]
                )
                compressor_summary[compressor_name]["avg_estimated_gas"].append(
                    results["avg_estimated_gas"]
                )
                compressor_summary[compressor_name]["total_transactions"] += results["total_transactions"]
        
        # Calculate final summary metrics
        for compressor_name, metrics in compressor_summary.items():
            self.results["summary"][compressor_name] = {
                "avg_compression_ratio": np.mean(metrics["avg_compression_ratio"]),
                "avg_encode_time_ms": np.mean(metrics["avg_encode_time_ms"]),
                "avg_decode_time_ms": np.mean(metrics["avg_decode_time_ms"]),
                "avg_estimated_gas": np.mean(metrics["avg_estimated_gas"]),
                "total_transactions": metrics["total_transactions"],
            }
        
        # Calculate rankings
        if len(compressor_summary) > 1:
            self._calculate_rankings()
    
    def _calculate_rankings(self) -> None:
        """Calculate rankings of compressors across different metrics"""
        metrics = ["avg_compression_ratio", "avg_encode_time_ms", "avg_decode_time_ms", "avg_estimated_gas"]
        reverse = [True, False, False, False]  # Higher is better for compression ratio, lower for others
        
        rankings = {}
        for metric, rev in zip(metrics, reverse):
            sorted_compressors = sorted(
                self.results["summary"].items(),
                key=lambda x: x[1][metric],
                reverse=rev
            )
            
            rankings[metric] = {
                comp[0]: idx + 1 for idx, comp in enumerate(sorted_compressors)
            }
        
        self.results["summary"]["rankings"] = rankings
    
    def _save_results(self) -> None:
        """Save benchmark results to files"""
        # Save detailed results as JSON
        detailed_path = os.path.join(self.output_dir, "detailed_results.json")
        with open(detailed_path, 'w') as f:
            json.dump(self.results["detailed"], f, indent=2)
        
        # Save summary results as JSON
        summary_path = os.path.join(self.output_dir, "summary_results.json")
        with open(summary_path, 'w') as f:
            json.dump(self.results["summary"], f, indent=2)
        
        # Save transaction type specific results
        txn_type_path = os.path.join(self.output_dir, "transaction_type_results.json")
        with open(txn_type_path, 'w') as f:
            json.dump(self.results["by_txn_type"], f, indent=2)
        
        logger.info(f"Saved benchmark results to {self.output_dir}")
    
    def _generate_visualizations(self) -> None:
        """Generate visualizations of benchmark results"""
        try:
            from visualization import generate_visualizations
            generate_visualizations(self.results, self.output_dir)
            logger.info(f"Generated visualizations in {self.output_dir}")
        except ImportError:
            logger.warning("Visualization module not found, skipping visualization generation")
            
            # Generate basic visualizations
            self._generate_basic_visualizations()
    
    def _generate_basic_visualizations(self) -> None:
        """Generate basic visualizations without the visualization module"""
        # Compression ratio comparison
        self._plot_comparison("avg_compression_ratio", "Compression Ratio", higher_is_better=True)
        
        # Encoding time comparison
        self._plot_comparison("avg_encode_time_ms", "Encoding Time (ms)", higher_is_better=False)
        
        # Gas cost comparison
        self._plot_comparison("avg_estimated_gas", "Estimated Gas Cost", higher_is_better=False)
        
        # Transaction type breakdown (if enough data)
        for dataset_name, dataset_results in self.results["by_txn_type"].items():
            self._plot_transaction_type_breakdown(dataset_name, dataset_results)
    
    def _plot_comparison(self, metric: str, title: str, higher_is_better: bool = True) -> None:
        """Plot comparison of compressors for a specific metric"""
        plt.figure(figsize=(10, 6))
        
        compressors = list(self.results["summary"].keys())
        if "rankings" in compressors:
            compressors.remove("rankings")
        
        values = [self.results["summary"][comp][metric] for comp in compressors]
        
        # Sort by value
        if higher_is_better:
            sorted_data = sorted(zip(compressors, values), key=lambda x: x[1], reverse=True)
        else:
            sorted_data = sorted(zip(compressors, values), key=lambda x: x[1])
        
        sorted_compressors, sorted_values = zip(*sorted_data)
        
        # Create color mapping
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        color_map = {
            compressor: colors[i % len(colors)] 
            for i, compressor in enumerate(sorted_compressors)
        }
        
        # Highlight ZeroCompress
        bar_colors = [
            'darkgreen' if comp == 'ZeroCompress' else color_map[comp] 
            for comp in sorted_compressors
        ]
        
        plt.bar(sorted_compressors, sorted_values, color=bar_colors)
        plt.title(title)
        plt.xlabel('Compressor')
        plt.ylabel(metric.replace('_', ' ').title())
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Add value labels
        for i, v in enumerate(sorted_values):
            plt.text(
                i, v, f"{v:.4f}" if abs(v) < 10 else f"{v:.1f}", 
                ha='center', va='bottom' if higher_is_better else 'top'
            )
        
        # Save plot
        plt.savefig(os.path.join(self.output_dir, f"{metric}_comparison.png"))
        plt.close()
    
    def _plot_transaction_type_breakdown(self, dataset_name: str, dataset_results: Dict[str, Any]) -> None:
        """Plot compression ratio breakdown by transaction type"""
        # Get all transaction types across all compressors
        all_tx_types = set()
        for compressor_results in dataset_results.values():
            all_tx_types.update(compressor_results.keys())
        
        # Skip if not enough transaction types
        if len(all_tx_types) <= 1:
            return
        
        # Create DataFrame for plotting
        data = []
        for compressor_name, compressor_results in dataset_results.items():
            for tx_type, tx_results in compressor_results.items():
                data.append({
                    "compressor": compressor_name,
                    "transaction_type": tx_type,
                    "compression_ratio": tx_results["avg_compression_ratio"],
                    "transaction_count": tx_results["transaction_count"],
                })
        
        df = pd.DataFrame(data)
        
        # Plot
        plt.figure(figsize=(12, 8))
        
        # Filter to top compressors if too many
        top_compressors = list(dataset_results.keys())
        if len(top_compressors) > 5:
            # Prioritize ZeroCompress and Sequence-CZIP
            if "ZeroCompress" in top_compressors:
                top_compressors.remove("ZeroCompress")
                selected = ["ZeroCompress"]
            else:
                selected = []
            
            if "Sequence-CZIP" in top_compressors:
                top_compressors.remove("Sequence-CZIP")
                selected.append("Sequence-CZIP")
            
            # Add remaining top compressors
            remaining_slots = 5 - len(selected)
            selected.extend(top_compressors[:remaining_slots])
            
            df = df[df['compressor'].isin(selected)]
        
        # Plot by transaction type
        pivot_df = df.pivot(index='transaction_type', columns='compressor', values='compression_ratio')
        ax = pivot_df.plot(kind='bar', figsize=(12, 8))
        
        plt.title(f"Compression Ratio by Transaction Type ({dataset_name})")
        plt.xlabel('Transaction Type')
        plt.ylabel('Compression Ratio')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Compressor')
        plt.tight_layout()
        
        # Save plot
        plt.savefig(os.path.join(self.output_dir, f"{dataset_name}_txtype_breakdown.png"))
        plt.close()


def main():
    """Main entry point for the benchmark runner"""
    parser = argparse.ArgumentParser(description='ZeroCompress Benchmarking Framework')
    parser.add_argument(
        '--config', 
        type=str, 
        default=os.path.join(os.path.dirname(__file__), 'configs', 'default.json'),
        help='Path to benchmark configuration file'
    )
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default=None,
        help='Directory to save benchmark results'
    )
    
    args = parser.parse_args()
    
    benchmark = CompressionBenchmark(args.config, args.output_dir)
    benchmark.load_standard_compressors()
    benchmark.run_benchmarks()
    
    logger.info("Benchmarking complete")


if __name__ == "__main__":
    main() 