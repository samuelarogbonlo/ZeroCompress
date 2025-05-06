# ZeroCompress Benchmarking Framework

A comprehensive framework for evaluating and comparing different compression techniques for Ethereum transaction data, with a focus on comparing ZeroCompress against other implementations like Sequence.xyz's CZIP.

## Overview

This benchmarking framework allows you to:

1. Compare multiple compression algorithms against standardized datasets
2. Measure key metrics: compression ratio, encoding time, decoding time, estimated gas costs
3. Analyze performance across different transaction types
4. Generate detailed reports and visualizations
5. Create fair comparisons with reference implementations

## Directory Structure

```
/benchmarking
├── benchmark_runner.py      # Main benchmarking script
├── configs/                 # Configuration files
│   └── default.json         # Default benchmarking configuration
├── data/                    # Test datasets (shared with data-collection)
├── implementations/         # Reference implementations
│   └── sequence_implementation.py  # Sequence.xyz CZIP reference
├── results/                 # Benchmark results
└── visualization/           # Visualization utilities
```

## Usage

### Basic Usage

Run the benchmark with the default configuration:

```bash
cd /path/to/ZeroCompress
python -m tools.benchmarking.benchmark_runner
```

### Custom Configuration

Specify a custom configuration file:

```bash
python -m tools.benchmarking.benchmark_runner --config tools/benchmarking/configs/my_config.json
```

### Output Directory

Specify a custom output directory for results:

```bash
python -m tools.benchmarking.benchmark_runner --output-dir results/my_benchmark
```

## Configuration

The benchmark is controlled by a JSON configuration file:

```json
{
  "name": "Benchmark Name",
  "description": "Benchmark description",
  "datasets": {
    "dataset_name": "path/to/dataset.json"
  },
  "compressors": {
    "CompressorName": {
      "enabled": true,
      "description": "Compressor description"
    }
  },
  "metrics": {
    "metric_name": {
      "weight": 0.5,
      "higher_is_better": true
    }
  }
}
```

### Key Configuration Options

- **datasets**: Map of dataset names to file paths
- **compressors**: Compressor implementations to evaluate
- **metrics**: Metrics to measure and their weights for scoring
- **visualization**: Chart generation options
- **benchmark_options**: Performance tuning options

## Adding Custom Compressors

To benchmark a custom compressor:

1. Create a Python class with `compress` and `decompress` methods
2. Register it with the benchmark runner:

```python
from my_compressor import MyCompressor

benchmark = CompressionBenchmark(config_path)
benchmark.register_compressor("MyCompressor", MyCompressor())
benchmark.run_benchmarks()
```

## Understanding Results

The benchmark produces:

1. **Summary Results**: Overall performance of each compressor
2. **Detailed Results**: Per-dataset performance metrics
3. **Transaction Type Results**: Performance breakdown by transaction type
4. **Visualizations**: Charts comparing different aspects of performance

### Key Metrics

- **Compression Ratio**: Percentage reduction in data size (higher is better)
- **Encoding Time**: Time to compress data (lower is better)
- **Decoding Time**: Time to decompress data (lower is better)
- **Estimated Gas**: Approximate gas cost for on-chain decompression (lower is better)

## Example Results

A typical output shows ZeroCompress compared to other implementations:

```
Results for ZeroCompress on arbitrum_sample:
Avg compression ratio: 0.7293
Encode time: 0.47ms
Decode time: 0.31ms
Est. gas: 12450

Comparison Sequence-CZIP vs ZeroCompress on arbitrum_sample:
Compression diff: -0.2214
Encode time ratio: 0.85x
Decode time ratio: 1.23x
Gas cost ratio: 1.45x
```

## Adding New Datasets

To add new test datasets:

1. Place the dataset JSON file in the `data` directory
2. Update your configuration file to include the new dataset
3. Run the benchmark with the updated configuration

## Reference Implementations

The benchmarking framework includes reference implementations of:

- **Sequence-CZIP**: A simplified model of Sequence.xyz's compression approach
- **ZeroCompress components**: Individual compression techniques used by ZeroCompress

These reference implementations allow for fair comparison against existing solutions.

## Contributing

To contribute to the benchmarking framework:

1. Add new compression techniques
2. Improve existing implementations
3. Add more realistic test datasets
4. Enhance visualization and reporting capabilities
5. Improve gas cost estimation models 