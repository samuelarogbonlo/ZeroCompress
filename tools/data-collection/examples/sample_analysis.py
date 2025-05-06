#!/usr/bin/env python3
"""
Sample analysis script for ZeroCompress

This script runs the complete analysis pipeline on the sample transaction data.
It demonstrates how to use the ZeroCompress analysis tools programmatically.
"""

import os
import sys
import logging

# Add parent directory to path to import scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.address_pattern_analyzer import AddressPatternAnalyzer
from scripts.zero_byte_analyzer import ZeroByteAnalyzer
from scripts.calldata_pattern_analyzer import CalldataPatternAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_analysis():
    """Run the complete analysis pipeline on sample data"""
    # Set paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_data_path = os.path.join(script_dir, '..', 'sample_data', 'sample_transactions.json')
    output_dir = os.path.join(script_dir, 'output', 'sample')
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("ZeroCompress Sample Analysis")
    logger.info("==========================")
    logger.info(f"Using sample data from: {sample_data_path}")
    logger.info(f"Saving results to: {output_dir}")
    
    try:
        # 1. Run address pattern analysis
        logger.info("\nStep 1: Analyzing address patterns...")
        address_output_dir = os.path.join(output_dir, 'address_analysis')
        os.makedirs(address_output_dir, exist_ok=True)
        
        address_analyzer = AddressPatternAnalyzer(sample_data_path, address_output_dir)
        
        # Analyze address frequency
        address_stats = address_analyzer.analyze_address_frequency()
        logger.info(f"- Address analysis: found {len(address_stats['top_addresses'])} frequently used addresses")
        logger.info(f"- Unique addresses: {address_stats['unique_addresses']}")
        logger.info(f"- Address reuse rate: {address_stats['address_reuse_rate']*100:.2f}%")
        logger.info(f"- Potential savings: {address_stats.get('potential_savings_percentage', 0):.2f}%")
        
        # Analyze calldata patterns
        calldata_stats = address_analyzer.analyze_address_patterns_in_calldata()
        logger.info(f"- Found {calldata_stats.get('total_embedded_addresses', 0)} addresses embedded in calldata")
        
        # Analyze temporal locality
        temporal_stats = address_analyzer.analyze_temporal_locality()
        
        # Combine results
        address_results = {
            'address_frequency_analysis': address_stats,
            'calldata_pattern_analysis': calldata_stats,
            'temporal_locality_analysis': temporal_stats,
        }
        
        # Save results
        address_result_file = address_analyzer.save_results(address_results)
        
        # Generate visualizations
        address_analyzer.generate_visualizations(address_stats, calldata_stats, 'sample')
        logger.info(f"- Address analysis results saved to: {address_result_file}")
        
        # 2. Run zero-byte pattern analysis
        logger.info("\nStep 2: Analyzing zero-byte patterns...")
        zero_byte_output_dir = os.path.join(output_dir, 'zero_byte_analysis')
        os.makedirs(zero_byte_output_dir, exist_ok=True)
        
        zero_analyzer = ZeroByteAnalyzer(sample_data_path, zero_byte_output_dir)
        
        # Analyze zero-byte patterns
        pattern_results = zero_analyzer.analyze_zero_byte_patterns()
        logger.info(f"- Zero-byte percentage: {pattern_results['zero_byte_percentage']:.2f}%")
        
        # Analyze transaction types
        type_results = zero_analyzer.analyze_transaction_types()
        logger.info(f"- Analyzed {type_results['total_types']} transaction types")
        
        # Analyze byte value distribution
        distribution_results = zero_analyzer.analyze_byte_value_distribution()
        logger.info(f"- Found {distribution_results['unique_byte_values']} unique byte values")
        
        # Calculate compression potential
        potential = pattern_results['compression_potential']
        logger.info(f"- Compression potential (simple): {potential['simple_encoding_savings_percentage']:.2f}%")
        logger.info(f"- Compression potential (RLE): {potential['rle_encoding_savings_percentage']:.2f}%")
        logger.info(f"- Compression potential (combined): {potential['combined_approach_savings_percentage']:.2f}%")
        
        # Combine results
        zero_byte_results = {
            'zero_byte_pattern_analysis': pattern_results,
            'transaction_type_analysis': type_results,
            'byte_distribution_analysis': distribution_results,
        }
        
        # Save results
        zero_byte_result_file = zero_analyzer.save_results(zero_byte_results)
        
        # Generate visualizations
        zero_analyzer.generate_visualizations(pattern_results, 'sample')
        logger.info(f"- Zero-byte analysis results saved to: {zero_byte_result_file}")
        
        # 3. Run calldata pattern analysis
        logger.info("\nStep 3: Analyzing calldata patterns...")
        calldata_output_dir = os.path.join(output_dir, 'calldata_analysis')
        os.makedirs(calldata_output_dir, exist_ok=True)
        
        calldata_analyzer = CalldataPatternAnalyzer(sample_data_path, calldata_output_dir)
        
        # Analyze function signatures
        function_results = calldata_analyzer.analyze_function_signatures()
        logger.info(f"- Found {function_results['unique_signatures']} unique function signatures")
        
        # Analyze parameter patterns
        parameter_results = calldata_analyzer.analyze_parameter_patterns()
        logger.info(f"- Analyzed parameters for {parameter_results['total_signatures_analyzed']} function signatures")
        
        # Analyze calldata structure
        structure_results = calldata_analyzer.analyze_calldata_structure()
        logger.info(f"- Analyzed structure of {structure_results['total_transactions']} transactions")
        
        # Analyze repeated patterns
        pattern_results = calldata_analyzer.analyze_repeated_patterns()
        ngram_analysis = pattern_results.get('ngram_analysis', {})
        for size, results in ngram_analysis.items():
            logger.info(f"- Found {results.get('common_patterns_count', 0)} common {size}-char patterns")
        
        # Combine results
        calldata_results = {
            'function_analysis': function_results,
            'parameter_analysis': parameter_results,
            'calldata_structure': structure_results,
            'repeated_patterns': pattern_results,
        }
        
        # Save results
        calldata_result_file = calldata_analyzer.save_results(calldata_results)
        
        # Generate visualizations
        calldata_analyzer.generate_visualizations(calldata_results, 'sample')
        logger.info(f"- Calldata analysis results saved to: {calldata_result_file}")
        
        # 4. Calculate overall compression potential
        logger.info("\nOverall Compression Potential:")
        address_savings = address_stats.get('potential_savings_percentage', 0)
        zero_savings = potential['combined_approach_savings_percentage']
        calldata_savings = structure_results.get('compression_estimate', {}).get('potential_savings_percentage', 0)
        
        # Simple weighted average
        overall_potential = (address_savings * 0.3 + zero_savings * 0.4 + calldata_savings * 0.3)
        
        logger.info(f"- Address compression: {address_savings:.2f}%")
        logger.info(f"- Zero-byte elimination: {zero_savings:.2f}%")
        logger.info(f"- Calldata optimization: {calldata_savings:.2f}%")
        logger.info(f"- Overall potential: {overall_potential:.2f}%")
        
        logger.info("\nAnalysis complete!")
        logger.info(f"All results saved to: {output_dir}")
        logger.info("Check the figures directories for visualizations")
        
    except Exception as e:
        logger.error(f"Error running analysis: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_analysis()) 