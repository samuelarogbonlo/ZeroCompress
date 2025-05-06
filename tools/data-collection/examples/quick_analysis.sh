#!/bin/bash
# Quick analysis script for ZeroCompress
# This script runs the entire data collection and analysis pipeline on a small dataset

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $SCRIPT_DIR/..

# Set variables
NETWORK="optimism"
OUTPUT_DIR="./examples/output"
BLOCKS=5
MAX_TXS=50

# Create output directory
mkdir -p $OUTPUT_DIR

echo "ZeroCompress Quick Analysis"
echo "=========================="
echo "Network: $NETWORK"
echo "Blocks: $BLOCKS"
echo "Max transactions: $MAX_TXS"
echo

# Step 1: Collect transaction data
echo "Step 1: Collecting transaction data..."
python scripts/transaction_collector.py \
  --network $NETWORK \
  --output-dir $OUTPUT_DIR \
  --blocks $BLOCKS \
  --max-transactions $MAX_TXS \
  --verbose

if [ $? -ne 0 ]; then
  echo "Error collecting transaction data"
  exit 1
fi

# Find the generated transaction file
TX_FILE=$(ls -t $OUTPUT_DIR/$NETWORK/*_transactions_*.json | head -1)
echo "Using transaction file: $TX_FILE"
echo

# Step 2: Run address pattern analysis
echo "Step 2: Analyzing address patterns..."
python scripts/address_pattern_analyzer.py \
  --input-file $TX_FILE \
  --output-dir $OUTPUT_DIR/$NETWORK/address_analysis \
  --output-prefix quick_analysis

if [ $? -ne 0 ]; then
  echo "Error analyzing address patterns"
  exit 1
fi

# Step 3: Run zero-byte pattern analysis
echo "Step 3: Analyzing zero-byte patterns..."
python scripts/zero_byte_analyzer.py \
  --input-file $TX_FILE \
  --output-dir $OUTPUT_DIR/$NETWORK/zero_byte_analysis \
  --output-prefix quick_analysis

if [ $? -ne 0 ]; then
  echo "Error analyzing zero-byte patterns"
  exit 1
fi

# Step 4: Run calldata pattern analysis
echo "Step 4: Analyzing calldata patterns..."
python scripts/calldata_pattern_analyzer.py \
  --input-file $TX_FILE \
  --output-dir $OUTPUT_DIR/$NETWORK/calldata_analysis \
  --output-prefix quick_analysis

if [ $? -ne 0 ]; then
  echo "Error analyzing calldata patterns"
  exit 1
fi

echo
echo "Analysis complete! Results are in $OUTPUT_DIR/$NETWORK/"
echo "Check the figures directory in each analysis folder for visualizations" 