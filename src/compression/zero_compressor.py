"""
ZeroCompressor - Main Compression Orchestrator

This module combines all compression techniques into a unified framework.
It coordinates the compression pipeline, determining which compression 
techniques to apply and in what order.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import os
import struct

# Import individual compression modules
from .address_compression import AddressCompressor as _AddressCompressor
from .zero_byte_compression import ZeroByteCompressor as _ZeroByteCompressor
from .function_selector_compression import FunctionSelectorCompressor as _FunctionSelectorCompressor
from .calldata_compression import CalldataCompressor as _CalldataCompressor


class ZeroCompressor:
    """
    Main compression orchestrator that combines multiple techniques
    to achieve maximum compression of Ethereum transaction data.
    
    The compression pipeline applies techniques in an optimal order:
    1. Function selector compression (first 4 bytes)
    2. Address compression (20-byte addresses) - Currently disabled for benchmark
    3. Pattern-based calldata compression
    4. Zero-byte compression
    
    Decompression is applied in reverse order.
    """
    
    # Compression technique markers
    TECHNIQUE_MARKERS = {
        'function_selector': 0xF1,
        'address': 0xF2,
        'calldata': 0xF3,
        'zero_byte': 0xF4,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ZeroCompressor with all sub-compressors
        
        Args:
            config: Optional configuration dictionary for customizing compressors
        """
        self.config = config or {}
        
        # Initialize individual compressors
        self.address_compressor = _AddressCompressor(
            max_addresses=self.config.get('max_addresses', 65536),
            index_bytes=self.config.get('address_index_bytes', 2)
        )
        
        self.zero_byte_compressor = _ZeroByteCompressor(
            min_sequence_length=self.config.get('min_zero_sequence', 3)
        )
        
        self.function_selector_compressor = _FunctionSelectorCompressor(
            max_selectors=self.config.get('max_selectors', 255)
        )
        
        self.calldata_compressor = _CalldataCompressor(
            dictionary_size=self.config.get('pattern_dictionary_size', 256)
        )
        
        # Compression flags - disable address compression for the benchmark
        self.flags = {
            'use_address_compression': False,  # Disabled for benchmark
            'use_zero_byte_compression': self.config.get('use_zero_byte_compression', True),
            'use_function_selector_compression': self.config.get('use_function_selector_compression', True),
            'use_calldata_compression': self.config.get('use_calldata_compression', True)
        }
        
        # Statistics
        self.stats = {
            'total_bytes_processed': 0,
            'total_bytes_compressed': 0,
            'compression_ratio': 0,
            'compression_breakdown': {}
        }
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress transaction data using all available techniques
        
        For benchmark simplicity, we'll use a format that's easier to decompress:
        [TECHNIQUE_MARKER][COMPRESSED_DATA]
        
        Args:
            data: Raw transaction data bytes
            
        Returns:
            Compressed data bytes
        """
        if not data:
            return data
        
        # Update statistics
        original_size = len(data)
        self.stats['total_bytes_processed'] += original_size
        
        # Track size at each compression stage
        stage_sizes = {'original': original_size}
        compressed_data = data
        
        # For benchmarking simplicity, we'll store the techniques applied
        applied_techniques = []
        
        # Stage 1: Function selector compression
        if self.flags['use_function_selector_compression'] and len(compressed_data) >= 4:
            # Extract function selector (first 4 bytes)
            selector = compressed_data[:4]
            rest_of_data = compressed_data[4:]
            
            # Compress selector
            compressed_selector, is_compressed = self.function_selector_compressor.compress_selector(selector)
            
            # If compressed, combine with marker
            if is_compressed:
                # For benchmark simplicity, mark the entire data as function-selector compressed
                compressed_data = bytes([self.TECHNIQUE_MARKERS['function_selector']]) + compressed_selector + rest_of_data
                applied_techniques.append('function_selector')
            
            stage_sizes['after_selector_compression'] = len(compressed_data)
        
        # Stage 2: Address compression (disabled for benchmark)
        if self.flags['use_address_compression']:
            # Build address dictionary if needed
            if not self.address_compressor.address_dict:
                addresses = self._extract_potential_addresses(compressed_data)
                if addresses:
                    self.address_compressor.build_dictionary(addresses)
            
            # Since address compression is complex and needs special markers,
            # we'll skip it for the benchmark
            stage_sizes['after_address_compression'] = len(compressed_data)
        
        # Stage 3: Calldata pattern compression
        calldata_to_compress = compressed_data
        if 'function_selector' in applied_techniques:
            # Skip the marker and process the rest
            calldata_to_compress = compressed_data[1:]
            
        if self.flags['use_calldata_compression']:
            # For benchmark simplicity, we'll apply calldata compression to the entire data
            # In a real implementation, we'd be more selective
            if not self.calldata_compressor.pattern_dict:
                # The calldata_compressor adapter initializes placeholder patterns
                pass
            
            calldata_compressed = self.calldata_compressor.compress(calldata_to_compress)
            
            # If compression was effective, use it
            if len(calldata_compressed) < len(calldata_to_compress):
                if 'function_selector' in applied_techniques:
                    # Preserve the function selector marker
                    compressed_data = bytes([self.TECHNIQUE_MARKERS['function_selector'], 
                                           self.TECHNIQUE_MARKERS['calldata']]) + calldata_compressed
                else:
                    compressed_data = bytes([self.TECHNIQUE_MARKERS['calldata']]) + calldata_compressed
                
                applied_techniques.append('calldata')
                
            stage_sizes['after_calldata_compression'] = len(compressed_data)
        
        # Stage 4: Zero-byte compression
        zero_byte_to_compress = compressed_data
        marker_count = len(applied_techniques)
        if marker_count > 0:
            # Skip the markers and process the rest
            zero_byte_to_compress = compressed_data[marker_count:]
            
        if self.flags['use_zero_byte_compression']:
            # Apply zero-byte compression to the remaining data
            zero_compressed = self.zero_byte_compressor.compress(zero_byte_to_compress)
            
            # If compression was effective, use it
            if len(zero_compressed) < len(zero_byte_to_compress):
                marker_bytes = compressed_data[:marker_count]
                compressed_data = marker_bytes + bytes([self.TECHNIQUE_MARKERS['zero_byte']]) + zero_compressed
                applied_techniques.append('zero_byte')
                
            stage_sizes['after_zero_byte_compression'] = len(compressed_data)
        
        # Update statistics
        compressed_size = len(compressed_data)
        self.stats['total_bytes_compressed'] += compressed_size
        
        # Calculate per-stage compression
        last_size = original_size
        for stage, size in stage_sizes.items():
            if stage != 'original':
                savings = last_size - size
                if stage not in self.stats['compression_breakdown']:
                    self.stats['compression_breakdown'][stage] = 0
                self.stats['compression_breakdown'][stage] += savings
                last_size = size
        
        return compressed_data
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """
        Decompress data compressed with ZeroCompressor
        
        For benchmark simplicity, we'll look for technique markers and
        apply the appropriate decompression in reverse order.
        
        Args:
            compressed_data: Compressed data bytes
            
        Returns:
            Decompressed data bytes
        """
        if not compressed_data:
            return compressed_data
        
        # Start with the compressed data
        data = compressed_data
        
        # Check for technique markers and apply decompression in reverse order
        # This simple approach works for the benchmark but wouldn't be sufficient
        # for a production system where techniques can be applied to different parts
        
        # First marker is for function selector
        if data and data[0] == self.TECHNIQUE_MARKERS['function_selector']:
            # Process function selector compression
            data = data[1:]  # Remove marker
            
            # Check for second marker (calldata)
            if data and data[0] == self.TECHNIQUE_MARKERS['calldata']:
                data = data[1:]  # Remove marker
                
                # Check for third marker (zero byte)
                if data and data[0] == self.TECHNIQUE_MARKERS['zero_byte']:
                    data = data[1:]  # Remove marker
                    
                    # Decompress zero bytes first
                    data = self.zero_byte_compressor.decompress(data)
                
                # Decompress calldata patterns
                data = self.calldata_compressor.decompress(data)
                
            elif data and data[0] == self.TECHNIQUE_MARKERS['zero_byte']:
                data = data[1:]  # Remove marker
                
                # Decompress zero bytes
                data = self.zero_byte_compressor.decompress(data)
            
            # Decompress function selector
            if data:
                first_byte = data[0]
                # Look up in the reverse dictionary
                reverse_dict = {idx: selector for selector, idx in self.function_selector_compressor.selector_dict.items()}
                
                if first_byte in reverse_dict:
                    # Decompress the selector
                    selector = reverse_dict[first_byte]
                    # Combine with rest of data
                    data = selector + data[1:]
                elif first_byte == self.function_selector_compressor.UNCOMPRESSED_MARKER and len(data) >= 5:
                    # Uncompressed marker + original selector, remove marker
                    data = data[1:]
        
        # Start with calldata marker
        elif data and data[0] == self.TECHNIQUE_MARKERS['calldata']:
            data = data[1:]  # Remove marker
            
            # Check for zero byte marker
            if data and data[0] == self.TECHNIQUE_MARKERS['zero_byte']:
                data = data[1:]  # Remove marker
                
                # Decompress zero bytes
                data = self.zero_byte_compressor.decompress(data)
            
            # Decompress calldata patterns
            data = self.calldata_compressor.decompress(data)
        
        # Start with zero byte marker
        elif data and data[0] == self.TECHNIQUE_MARKERS['zero_byte']:
            data = data[1:]  # Remove marker
            
            # Decompress zero bytes
            data = self.zero_byte_compressor.decompress(data)
        
        return data
    
    def _extract_potential_addresses(self, data: bytes) -> List[str]:
        """
        Extract potential Ethereum addresses from transaction data
        This is a simplified implementation for demo purposes
        
        Args:
            data: Transaction data bytes
            
        Returns:
            List of potential addresses as hex strings
        """
        addresses = []
        
        # Simplistic approach: look for 20-byte chunks that could be addresses
        # In production, we'd use more sophisticated heuristics
        if len(data) >= 20:
            # Standard length for most ERC20 functions (selector + address + value)
            if len(data) >= 4 + 20 + 32:
                # ERC20 transfer/approve pattern: selector(4) + address(20) + value(32)
                selector = data[:4]
                erc20_patterns = [
                    b"\xa9\x05\x9c\xbb",  # transfer
                    b"\x09\x5e\xa7\xb3",  # approve
                    b"\x23\xb8\x72\xdd",  # transferFrom (this has 2 addresses)
                ]
                
                if selector in erc20_patterns:
                    # Extract address from ERC20 function call
                    potential_addr = data[4:24]  # First address
                    addr_hex = '0x' + potential_addr.hex()
                    addresses.append(addr_hex)
                    
                    # Check for transferFrom which has two addresses
                    if selector == b"\x23\xb8\x72\xdd" and len(data) >= 4 + 20 + 20 + 32:
                        second_addr = data[24:44]  # Second address
                        addr_hex = '0x' + second_addr.hex()
                        addresses.append(addr_hex)
            
            # Scan for other potential addresses
            for i in range(0, len(data) - 20, 20):
                potential_addr = data[i:i+20]
                
                # Simple heuristic: addresses are unlikely to have many high bytes
                high_bytes = sum(1 for b in potential_addr if b > 240)
                if high_bytes <= 4:
                    addr_hex = '0x' + potential_addr.hex()
                    if addr_hex not in addresses:
                        addresses.append(addr_hex)
        
        return addresses
    
    def _apply_address_compression(self, data: bytes) -> bytes:
        """
        Apply address compression to transaction data
        
        Args:
            data: Transaction data
            
        Returns:
            Data with addresses compressed
        """
        if not data or len(data) < 20 or not self.address_compressor.address_dict:
            return data
        
        result = bytearray()
        i = 0
        
        # Check for calldata pattern: function selector followed by addresses and data
        if len(data) >= 24:  # At least selector + address
            # First preserve function selector or compressed selector
            selector_len = 1 if len(data[0:1]) == 1 and data[0] < 128 else 4
            result.extend(data[:selector_len])
            i = selector_len
        
        # Process the rest of the data
        while i <= len(data) - 20:
            found_address = False
            
            # Check if current position contains an address
            potential_addr = data[i:i+20]
            addr_hex = '0x' + potential_addr.hex()
            
            # Try to compress
            compressed, is_compressed = self.address_compressor.compress_address(addr_hex)
            
            if is_compressed:
                # Address was compressed
                result.extend(compressed)
                i += 20
                found_address = True
            
            if not found_address:
                # Not an address or not compressible, add one byte and continue
                result.append(data[i])
                i += 1
        
        # Add any remaining bytes
        if i < len(data):
            result.extend(data[i:])
        
        return bytes(result)
    
    def _apply_address_decompression(self, data: bytes) -> bytes:
        """
        Apply address decompression
        
        Args:
            data: Compressed data
            
        Returns:
            Data with addresses decompressed
        """
        # This is a simplified implementation
        # In production, we'd need proper markers to identify compressed addresses
        
        # For the prototype, we'll just return the input data
        # A full implementation would require a more complex approach with marker bytes
        return data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        # Calculate overall compression ratio
        if self.stats['total_bytes_processed'] > 0:
            self.stats['compression_ratio'] = 1 - (self.stats['total_bytes_compressed'] / self.stats['total_bytes_processed'])
        
        # Gather stats from individual compressors
        self.stats['address_compressor'] = self.address_compressor.get_stats()
        self.stats['zero_byte_compressor'] = self.zero_byte_compressor.get_stats()
        self.stats['function_selector_compressor'] = self.function_selector_compressor.get_stats()
        self.stats['calldata_compressor'] = self.calldata_compressor.get_stats()
        
        return self.stats 