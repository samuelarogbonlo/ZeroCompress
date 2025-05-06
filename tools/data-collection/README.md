# ZeroCompress Data Collection and Analysis Tools

This directory contains tools for collecting and analyzing transaction data from Ethereum L2 networks to identify compression opportunities.

## Overview

The ZeroCompress data collection framework consists of several Python scripts designed to:

1. Collect transaction data from L2 networks (Arbitrum, Optimism, Base)
2. Analyze various patterns in transaction data
3. Identify compression opportunities
4. Quantify potential savings from different compression techniques

## Tools

### Data Collection

- **transaction_collector.py**: Collects transaction data from L2 networks using RPC endpoints or block explorer APIs.

### Data Analysis

- **address_pattern_analyzer.py**: Analyzes patterns in address usage to identify compression opportunities.
- **zero_byte_analyzer.py**: Analyzes zero-byte patterns and their potential for compression.
- **calldata_pattern_analyzer.py**: Analyzes patterns in calldata, including function signatures and parameters.

### Runner Script

- **run_analysis.py**: Orchestrates the running of all tools in a complete pipeline.

## Requirements

- Python 3.7+
- Required packages: web3, pandas, numpy, matplotlib, requests, tqdm

Install requirements:

```
pip install web3 pandas numpy matplotlib requests tqdm
```

## Usage

### Running the Complete Pipeline

To run the complete analysis pipeline:

```
python scripts/run_analysis.py --network arbitrum --blocks 100 --max-txs 10000
```

This will:
1. Collect transaction data from Arbitrum
2. Run all analysis tools
3. Generate a summary report

### Individual Tools

Each tool can also be run independently:

#### Transaction Collection

```
python scripts/run_analysis.py --mode collect --network optimism --blocks 50
```

#### Address Analysis

```
python scripts/run_analysis.py --mode address --input-file path/to/transactions.json
```

#### Zero-Byte Analysis

```
python scripts/run_analysis.py --mode zero --input-file path/to/transactions.json
```

#### Calldata Analysis

```
python scripts/run_analysis.py --mode calldata --input-file path/to/transactions.json
```

## Output

The tools generate the following outputs:

1. JSON files with detailed analysis results
2. Visualizations in PNG format
3. Summary reports in Markdown format

All outputs are organized in the output directory specified (defaults to `./analysis_results`).

## Advanced Configuration

For more advanced configuration options, run any script with the `--help` flag to see all available options.

## Contributing

When contributing to these tools:

1. Follow the existing code style
2. Add appropriate documentation
3. Write tests for new functionality
4. Ensure backward compatibility

## License

These tools are part of the ZeroCompress project and are subject to the same license terms as the overall project. 