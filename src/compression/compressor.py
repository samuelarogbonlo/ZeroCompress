"""
ZeroCompress Main Module

This module provides the main ZeroCompressor class that combines all
compression techniques into a unified interface.
"""

from typing import Dict, List, Tuple, Optional, Union, Any, Set
import json
import os

from .address_compression import AddressCompressor
from .zero_byte_compression import ZeroByteCompressor
from .function_selector_compression import FunctionSelectorCompressor


class ZeroCompressor:
    """
    Main compressor class that combines all ZeroCompress techniques.
    
    This class orchestrates the application of multiple compression techniques
    and handles the compression format structure.
    """
    
    # Compression format version
    FORMAT_VERSION = 1
    
    # Compression flags (bit mask)
    FLAG_ZERO_BYTE_COMPRESSION = 0x01
    FLAG_ADDRESS_COMPRESSION = 0x02
    FLAG_FUNCTION_SELECTOR_COMPRESSION = 0x04
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ZeroCompressor with optional configuration

        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize component compressors
        self.address_compressor = AddressCompressor()
        self.zero_byte_compressor = ZeroByteCompressor()
        self.function_selector_compressor = FunctionSelectorCompressor()
        
        # Compression statistics
        self.stats = {
            'total_txs_processed': 0,
            'total_bytes_processed': 0,
            'total_bytes_compressed': 0,
            'compression_ratio': 0,
        }
        
        # Load configuration if provided
        if config_path:
            self.load_config(config_path)
    
    def compress_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress a full Ethereum transaction

        Args:
            tx_data: Transaction data dictionary with 'input', 'to', 'from', etc.

        Returns:
            Compressed transaction data
        """
        # Clone the transaction data
        compressed_tx = tx_data.copy()
        
        # Skip if no input data
        if not tx_data.get('input') or tx_data.get('input') == '0x':
            return compressed_tx
        
        # Convert input to bytes
        input_data = tx_data['input']
        if input_data.startswith('0x'):
            input_data = input_data[2:]
        
        input_bytes = bytes.fromhex(input_data)
        
        # Update statistics
        self.stats['total_txs_processed'] += 1
        self.stats['total_bytes_processed'] += len(input_bytes)
        
        # Initialize compression flags
        compression_flags = 0x00
        
        # Apply compression techniques
        compressed_bytes = input_bytes
        
        # 1. Function selector compression
        if len(compressed_bytes) >= 4:
            # Only attempt if the input has a function selector
            compressed_bytes = self.function_selector_compressor.compress_calldata(compressed_bytes)
            compression_flags |= self.FLAG_FUNCTION_SELECTOR_COMPRESSION
        
        # 2. Address compression
        # Extract 'to' and 'from' addresses
        to_address = tx_data.get('to')
        from_address = tx_data.get('from')
        
        # Add addresses to compressor dictionary for future use
        if to_address and from_address:
            self.address_compressor.build_dictionary([to_address, from_address])
        
        # Attempt to compress addresses in calldata
        compressed_bytes = self.compress_addresses_in_calldata(compressed_bytes)
        compression_flags |= self.FLAG_ADDRESS_COMPRESSION
        
        # 3. Zero-byte compression
        if self.zero_byte_compressor.is_compressible(compressed_bytes):
            compressed_bytes = self.zero_byte_compressor.compress(compressed_bytes)
            compression_flags |= self.FLAG_ZERO_BYTE_COMPRESSION
        
        # Generate compressed calldata format
        # [Version(1B)][Flags(1B)][Compressed Data...]
        format_header = bytes([self.FORMAT_VERSION, compression_flags])
        final_compressed = format_header + compressed_bytes
        
        # Update the transaction data with compressed input
        compressed_tx['input'] = '0x' + final_compressed.hex()
        
        # Update statistics
        self.stats['total_bytes_compressed'] += len(final_compressed)
        
        return compressed_tx
    
    def decompress_transaction(self, compressed_tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress a compressed Ethereum transaction

        Args:
            compressed_tx: Compressed transaction data

        Returns:
            Decompressed transaction data
        """
        # Clone the transaction data
        decompressed_tx = compressed_tx.copy()
        
        # Skip if no input data
        if not compressed_tx.get('input') or compressed_tx.get('input') == '0x':
            return decompressed_tx
        
        # Convert input to bytes
        input_data = compressed_tx['input']
        if input_data.startswith('0x'):
            input_data = input_data[2:]
        
        input_bytes = bytes.fromhex(input_data)
        
        # Check if it's a compressed input (has format header)
        if len(input_bytes) < 2:
            # Too short to be compressed, return as-is
            return decompressed_tx
        
        # Extract format header
        version = input_bytes[0]
        flags = input_bytes[1]
        
        # Check version compatibility
        if version != self.FORMAT_VERSION:
            # Unsupported version, return as-is and log warning
            print(f"Warning: Unsupported compression format version: {version}")
            return decompressed_tx
        
        # Extract compressed data
        compressed_bytes = input_bytes[2:]
        
        # Apply decompression techniques in reverse order
        decompressed_bytes = compressed_bytes
        
        # 1. Zero-byte decompression
        if flags & self.FLAG_ZERO_BYTE_COMPRESSION:
            decompressed_bytes = self.zero_byte_compressor.decompress(decompressed_bytes)
        
        # 2. Address decompression
        if flags & self.FLAG_ADDRESS_COMPRESSION:
            decompressed_bytes = self.decompress_addresses_in_calldata(decompressed_bytes)
        
        # 3. Function selector decompression
        if flags & self.FLAG_FUNCTION_SELECTOR_COMPRESSION:
            decompressed_bytes = self.function_selector_compressor.decompress_calldata(decompressed_bytes)
        
        # Update the transaction data with decompressed input
        decompressed_tx['input'] = '0x' + decompressed_bytes.hex()
        
        return decompressed_tx
    
    def compress_addresses_in_calldata(self, calldata: bytes) -> bytes:
        """
        Apply address compression to calldata

        Args:
            calldata: Raw calldata bytes

        Returns:
            Calldata with addresses compressed
        """
        # This is a simplified implementation
        # A full implementation would need to parse the ABI structure
        return self.address_compressor.compress_addresses_in_calldata(calldata)
    
    def decompress_addresses_in_calldata(self, compressed_calldata: bytes) -> bytes:
        """
        Decompress addresses in compressed calldata

        Args:
            compressed_calldata: Calldata with compressed addresses

        Returns:
            Calldata with addresses decompressed
        """
        # This is a simplified implementation
        # A full implementation would need to parse the compressed format
        return compressed_calldata
    
    def train_on_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        """
        Train the compressor on a set of transactions to build dictionaries

        Args:
            transactions: List of transaction data dictionaries
        """
        # Extract function selectors
        selectors = []
        for tx in transactions:
            input_data = tx.get('input', '')
            if input_data and input_data != '0x' and len(input_data) >= 10:
                if input_data.startswith('0x'):
                    selector = bytes.fromhex(input_data[2:10])
                else:
                    selector = bytes.fromhex(input_data[:8])
                selectors.append(selector)
        
        # Build function selector dictionary
        self.function_selector_compressor.build_dictionary(selectors)
        
        # Extract addresses
        addresses = []
        for tx in transactions:
            to_address = tx.get('to')
            from_address = tx.get('from')
            if to_address:
                addresses.append(to_address)
            if from_address:
                addresses.append(from_address)
        
        # Build address dictionary
        self.address_compressor.build_dictionary(addresses)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined compression statistics"""
        # Calculate overall compression ratio
        if self.stats['total_bytes_processed'] > 0:
            self.stats['compression_ratio'] = 1 - (self.stats['total_bytes_compressed'] / self.stats['total_bytes_processed'])
        
        # Get component stats
        self.stats['address_compression'] = self.address_compressor.get_stats()
        self.stats['zero_byte_compression'] = self.zero_byte_compressor.get_stats()
        self.stats['function_selector_compression'] = self.function_selector_compressor.get_stats()
        
        return self.stats
    
    def save_config(self, filepath: str) -> None:
        """
        Save compression configuration to a file

        Args:
            filepath: Path to save the configuration
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save component dictionaries
        config_dir = os.path.dirname(filepath)
        
        # Save dictionaries in the same directory
        address_dict_path = os.path.join(config_dir, 'address_dictionary.json')
        self.address_compressor.save_dictionary(address_dict_path)
        
        selector_dict_path = os.path.join(config_dir, 'selector_dictionary.json')
        self.function_selector_compressor.save_dictionary(selector_dict_path)
        
        # Save zero-byte stats
        zero_byte_stats_path = os.path.join(config_dir, 'zero_byte_stats.json')
        self.zero_byte_compressor.save_stats(zero_byte_stats_path)
        
        # Save main configuration
        config = {
            'format_version': self.FORMAT_VERSION,
            'address_dictionary_path': address_dict_path,
            'selector_dictionary_path': selector_dict_path,
            'zero_byte_stats_path': zero_byte_stats_path,
            'stats': self.get_stats()
        }
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_config(self, filepath: str) -> None:
        """
        Load compression configuration from a file

        Args:
            filepath: Path to load the configuration from
        """
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        # Load component dictionaries
        if 'address_dictionary_path' in config:
            self.address_compressor.load_dictionary(config['address_dictionary_path'])
        
        if 'selector_dictionary_path' in config:
            self.function_selector_compressor.load_dictionary(config['selector_dictionary_path'])
        
        # Load stats
        if 'stats' in config:
            self.stats = config['stats'] 