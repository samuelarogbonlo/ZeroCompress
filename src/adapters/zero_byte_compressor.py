"""
ZeroByteCompressor Adapter

This adapter implements the zero-byte run-length compression technique
used in ZeroCompress.
"""

from typing import Dict, List, Tuple, Optional, Any


class ZeroByteCompressor:
    """
    Implementation of the zero-byte run-length compression algorithm.
    
    This compressor finds sequences of zero bytes (0x00) and replaces them
    with a marker byte followed by a count byte to reduce space.
    """
    
    def __init__(self, min_sequence_length: int = 3):
        """
        Initialize the zero-byte compressor
        
        Args:
            min_sequence_length: Minimum sequence of zeros to compress
        """
        self.min_sequence_length = min_sequence_length
        
        # Zero run marker byte
        self.ZERO_RUN_MARKER = 0xF0
        
        # Statistics
        self.stats = {
            'total_bytes_processed': 0,
            'total_bytes_compressed': 0,
            'zero_runs_compressed': 0,
            'zero_bytes_compressed': 0,
            'bytes_saved': 0
        }
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress data by replacing runs of zero bytes
        
        Args:
            data: Input data bytes
            
        Returns:
            Compressed data bytes
        """
        if not data:
            return data
        
        # Update statistics
        self.stats['total_bytes_processed'] += len(data)
        
        result = bytearray()
        i = 0
        
        while i < len(data):
            # Check for zero run
            if data[i] == 0:
                # Count consecutive zeros
                zero_count = 0
                while i + zero_count < len(data) and data[i + zero_count] == 0:
                    zero_count += 1
                    if zero_count == 255:  # Maximum representable in one byte
                        break
                
                # If run is long enough, compress it
                if zero_count >= self.min_sequence_length:
                    # Add marker + count
                    result.extend([self.ZERO_RUN_MARKER, zero_count])
                    
                    # Update statistics
                    self.stats['zero_runs_compressed'] += 1
                    self.stats['zero_bytes_compressed'] += zero_count
                    self.stats['bytes_saved'] += zero_count - 2  # 2 bytes for marker + count
                    
                    # Move index past the zeros
                    i += zero_count
                else:
                    # Run too short, copy the zeros
                    for _ in range(zero_count):
                        result.append(0)
                    i += zero_count
            else:
                # Handle case where byte matches our marker
                if data[i] == self.ZERO_RUN_MARKER:
                    # Escape the marker by doubling it
                    result.extend([self.ZERO_RUN_MARKER, 0])
                else:
                    # Normal byte, just copy
                    result.append(data[i])
                i += 1
        
        compressed_data = bytes(result)
        self.stats['total_bytes_compressed'] += len(compressed_data)
        
        return compressed_data
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data with zero run compression
        
        Args:
            data: Compressed data bytes
            
        Returns:
            Decompressed data bytes
        """
        if not data:
            return data
        
        result = bytearray()
        i = 0
        
        while i < len(data):
            # Check for zero run marker
            if data[i] == self.ZERO_RUN_MARKER:
                if i + 1 < len(data):
                    count = data[i+1]
                    
                    if count == 0:
                        # Escaped marker
                        result.append(self.ZERO_RUN_MARKER)
                    else:
                        # Zero run, expand it
                        result.extend([0] * count)
                    
                    i += 2  # Skip marker and count/escape
                else:
                    # Marker at end of data, just copy it
                    result.append(data[i])
                    i += 1
            else:
                # Normal byte, just copy
                result.append(data[i])
                i += 1
        
        return bytes(result)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        # Calculate overall compression ratio if data was processed
        if self.stats['total_bytes_processed'] > 0:
            ratio = 1 - (self.stats['total_bytes_compressed'] / self.stats['total_bytes_processed'])
            self.stats['compression_ratio'] = ratio
        
        return self.stats 