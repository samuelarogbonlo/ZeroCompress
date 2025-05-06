"""
Zero-Byte Compressor Adapter

This module adapts the zero_byte_compression.py interface to the naming
convention expected by the benchmarking framework.
"""

from .zero_byte_compression import ZeroByteCompressor as _ZeroByteCompressor


class ZeroByteCompressor:
    """
    Adapter for the ZeroByteCompressor class from zero_byte_compression.py
    Provides the compress and decompress methods expected by the benchmarking framework
    """
    
    def __init__(self):
        """Initialize the zero-byte compressor"""
        self.compressor = _ZeroByteCompressor(min_sequence_length=3)
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress data by encoding sequences of zero bytes
        
        Args:
            data: Raw data bytes to compress
            
        Returns:
            Compressed data bytes
        """
        return self.compressor.compress(data)
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """
        Decompress data compressed with ZeroByteCompressor
        
        Args:
            compressed_data: Compressed data bytes
            
        Returns:
            Decompressed data bytes
        """
        return self.compressor.decompress(compressed_data) 