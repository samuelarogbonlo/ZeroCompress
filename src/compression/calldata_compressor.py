"""
Calldata Compressor Adapter

This module adapts the calldata_compression.py interface to the naming
convention expected by the benchmarking framework.
"""

from .calldata_compression import CalldataCompressor as _CalldataCompressor


class CalldataCompressor:
    """
    Adapter for the CalldataCompressor class from calldata_compression.py
    Provides the compress and decompress methods expected by the benchmarking framework
    """
    
    def __init__(self):
        """Initialize the calldata compressor"""
        self.compressor = _CalldataCompressor(dictionary_size=256)
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress calldata using pattern recognition
        
        Args:
            data: Raw calldata bytes to compress
            
        Returns:
            Compressed calldata bytes
        """
        # For benchmark purposes, we need some pre-built dictionary
        # In a real implementation, this would be built from large datasets
        if not self.compressor.pattern_dict:
            # Create some placeholder patterns
            # These would normally be derived from analysis of many transactions
            placeholder_patterns = {}
            
            # Common patterns in calldata
            patterns = [
                # Common fixed-length type encoding patterns
                bytes.fromhex("0000000000000000000000000000000000000000"),  # Zero address (20 bytes)
                bytes.fromhex("00000000000000000000000000000000"),          # Zero uint256 (32 bytes)
                bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000001"),  # uint256(1)
                bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000"),    # uint256(0) pad
                
                # ERC20 common patterns
                bytes.fromhex("000000000000000000000000"),  # Address padding prefix
                bytes.fromhex("00000000000000000000000000000000000000000000000000000000"),  # Amount padding
                
                # Uniswap-style patterns
                bytes.fromhex("000000000000000000000000000000000000000000000000"),  # Common in Uniswap data
                bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000"),  # Array encoding
            ]
            
            for i, pattern in enumerate(patterns):
                placeholder_patterns[pattern] = i
            
            self.compressor.pattern_dict = placeholder_patterns
        
        return self.compressor.compress(data)
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """
        Decompress data compressed with CalldataCompressor
        
        Args:
            compressed_data: Compressed calldata bytes
            
        Returns:
            Decompressed calldata bytes
        """
        return self.compressor.decompress(compressed_data) 