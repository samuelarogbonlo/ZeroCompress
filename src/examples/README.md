# ZeroCompress Example Scripts

This directory contains example scripts demonstrating how to use the ZeroCompress library for Ethereum calldata compression.

## Available Examples

- `compression_example.py`: Demonstrates the full compression pipeline including training, compressing transactions, and viewing statistics

## Requirements

Make sure you have installed the required packages:

```bash
pip install -r ../requirements.txt
```

## Running the Examples

To run an example script:

```bash
cd /path/to/ZeroCompress/src
python -m examples.compression_example
```

## Example Output

The compression example demonstrates:
- Training compressors with sample data
- Compressing transaction calldata
- Decompressing data to verify correctness
- Viewing compression statistics
- Saving compression dictionaries for later use

The output will show statistics for each transaction, including:
- Original and compressed calldata size
- Bytes saved and compression ratio
- Verification of correct decompression
- Overall compression statistics 