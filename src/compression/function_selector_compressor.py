"""
Function Selector Compressor Adapter

This module adapts the function_selector_compression.py interface to the naming
convention expected by the benchmarking framework.
"""

from .function_selector_compression import FunctionSelectorCompressor as _FunctionSelectorCompressor


class FunctionSelectorCompressor:
    """
    Adapter for the FunctionSelectorCompressor class from function_selector_compression.py
    Provides the compress and decompress methods expected by the benchmarking framework
    """
    
    # Common EVM function selectors
    COMMON_SELECTORS = {
        bytes.fromhex("a9059cbb"): 0,  # transfer(address,uint256)
        bytes.fromhex("095ea7b3"): 1,  # approve(address,uint256)
        bytes.fromhex("23b872dd"): 2,  # transferFrom(address,address,uint256)
        bytes.fromhex("70a08231"): 3,  # balanceOf(address)
        bytes.fromhex("dd62ed3e"): 4,  # allowance(address,address)
        bytes.fromhex("18160ddd"): 5,  # totalSupply()
        bytes.fromhex("313ce567"): 6,  # decimals()
        bytes.fromhex("06fdde03"): 7,  # name()
        bytes.fromhex("95d89b41"): 8,  # symbol()
    }
    
    def __init__(self):
        """Initialize the function selector compressor"""
        self.compressor = _FunctionSelectorCompressor(max_selectors=255)
        
        # Pre-build selector dictionary with common selectors
        selectors = list(self.COMMON_SELECTORS.keys())
        self.compressor.build_dictionary(selectors)
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress transaction data by optimizing function selectors
        
        Args:
            data: Raw transaction data bytes
            
        Returns:
            Compressed data bytes
        """
        # Extract function selector if present
        if len(data) < 4:
            return data
        
        selector = data[:4]
        rest_of_data = data[4:]
        
        # Try to compress the selector
        compressed_selector, is_compressed = self.compressor.compress_selector(selector)
        
        if is_compressed:
            # Return compressed selector + rest of data
            return compressed_selector + rest_of_data
        else:
            # Function selector was not compressible
            return data
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """
        Decompress data compressed with FunctionSelectorCompressor
        
        Args:
            compressed_data: Compressed data bytes
            
        Returns:
            Decompressed data bytes
        """
        if not compressed_data or len(compressed_data) < 1:
            return compressed_data
        
        # Check if the first byte is a compressed selector
        first_byte = compressed_data[0]
        
        # If the byte looks like a compressed selector (0-254, not 0xFF which is the uncompressed marker)
        if first_byte < 255:
            # Look up in the reverse dictionary
            reverse_dict = {idx: selector for selector, idx in self.compressor.selector_dict.items()}
            
            if first_byte in reverse_dict:
                # Decompress the selector
                selector = reverse_dict[first_byte]
                # Return decompressed selector + rest of data
                return selector + compressed_data[1:]
        
        # Not a compressed selector or not recognized
        return compressed_data 