"""
Zero-Byte Compression Module

This module implements techniques for compressing sequences of zero bytes
in Ethereum calldata, which are very common in transaction data.
"""

from typing import Dict, List, Tuple, Optional, Any
import json
import os


class ZeroByteCompressor:
    """
    Compresses sequences of zero bytes in Ethereum calldata.
    
    Techniques used:
    1. Run-length encoding: Replace sequences of zeros with (marker, length)
    2. Specialized markers: Different markers for different length ranges
    3. Skip small sequences: Don't compress sequences that would grow in size
    """
    
    # Constants
    ZERO_BYTE = 0x00
    
    # Compression markers
    # Using uncommon values that are unlikely to appear in normal calldata
    RLE_MARKER_SHORT = 0xF0  # For sequences of 3-255 zeros (2 bytes total)
    RLE_MARKER_MEDIUM = 0xF1  # For sequences of 256-65535 zeros (3 bytes total)
    RLE_MARKER_LONG = 0xF2  # For sequences > 65535 zeros (5 bytes total)
    
    def __init__(self, min_sequence_length: int = 3):
        """
        Initialize the zero-byte compressor

        Args:
            min_sequence_length: Minimum sequence length to compress (default: 3)
                For sequences of length 2, compression would increase size
        """
        self.min_sequence_length = min_sequence_length
        
        # Statistics
        self.stats = {
            'total_bytes_processed': 0,
            'total_zero_bytes': 0,
            'sequences_compressed': 0,
            'bytes_saved': 0
        }
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress data by encoding sequences of zero bytes

        Args:
            data: Raw data bytes to compress

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
            # Check if current byte is zero
            if data[i] == self.ZERO_BYTE:
                # Count consecutive zeros
                start = i
                while i < len(data) and data[i] == self.ZERO_BYTE:
                    i += 1
                
                sequence_length = i - start
                self.stats['total_zero_bytes'] += sequence_length
                
                # Compress if sequence is long enough
                if sequence_length >= self.min_sequence_length:
                    result.extend(self._encode_zero_sequence(sequence_length))
                    self.stats['sequences_compressed'] += 1
                    
                    # Calculate bytes saved
                    if sequence_length <= 255:
                        # Encoded as [F0, length] (2 bytes)
                        bytes_saved = sequence_length - 2
                    elif sequence_length <= 65535:
                        # Encoded as [F1, length_high, length_low] (3 bytes)
                        bytes_saved = sequence_length - 3
                    else:
                        # Encoded as [F2, length_byte3, length_byte2, length_byte1, length_byte0] (5 bytes)
                        bytes_saved = sequence_length - 5
                    
                    if bytes_saved > 0:
                        self.stats['bytes_saved'] += bytes_saved
                else:
                    # Sequence too short to compress, add as-is
                    result.extend([self.ZERO_BYTE] * sequence_length)
            else:
                # Non-zero byte, add as-is
                result.append(data[i])
                i += 1
        
        return bytes(result)
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data by decoding zero-byte sequences

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
            # Check for compression markers
            if i < len(data) - 1 and data[i] == self.RLE_MARKER_SHORT:
                # Short sequence: [F0, length]
                length = data[i + 1]
                result.extend([self.ZERO_BYTE] * length)
                i += 2
            elif i < len(data) - 2 and data[i] == self.RLE_MARKER_MEDIUM:
                # Medium sequence: [F1, length_high, length_low]
                length = (data[i + 1] << 8) | data[i + 2]
                result.extend([self.ZERO_BYTE] * length)
                i += 3
            elif i < len(data) - 4 and data[i] == self.RLE_MARKER_LONG:
                # Long sequence: [F2, length_byte3, length_byte2, length_byte1, length_byte0]
                length = (data[i + 1] << 24) | (data[i + 2] << 16) | (data[i + 3] << 8) | data[i + 4]
                result.extend([self.ZERO_BYTE] * length)
                i += 5
            else:
                # Regular byte, add as-is
                result.append(data[i])
                i += 1
        
        return bytes(result)
    
    def _encode_zero_sequence(self, length: int) -> bytes:
        """
        Encode a sequence of zero bytes

        Args:
            length: Length of the zero-byte sequence

        Returns:
            Encoded representation of the sequence
        """
        if length <= 255:
            # Short sequence: [F0, length]
            return bytes([self.RLE_MARKER_SHORT, length])
        elif length <= 65535:
            # Medium sequence: [F1, length_high, length_low]
            return bytes([self.RLE_MARKER_MEDIUM, (length >> 8) & 0xFF, length & 0xFF])
        else:
            # Long sequence: [F2, length_byte3, length_byte2, length_byte1, length_byte0]
            return bytes([
                self.RLE_MARKER_LONG,
                (length >> 24) & 0xFF,
                (length >> 16) & 0xFF,
                (length >> 8) & 0xFF,
                length & 0xFF
            ])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        # Calculate additional stats
        if self.stats['total_bytes_processed'] > 0:
            self.stats['zero_byte_percentage'] = (self.stats['total_zero_bytes'] / self.stats['total_bytes_processed']) * 100
            self.stats['compression_ratio'] = 1 - ((self.stats['total_bytes_processed'] - self.stats['bytes_saved']) / self.stats['total_bytes_processed'])
        
        return self.stats
    
    def save_stats(self, filepath: str) -> None:
        """
        Save compression statistics to a file

        Args:
            filepath: Path to save the statistics
        """
        with open(filepath, 'w') as f:
            json.dump(self.get_stats(), f, indent=2)
    
    def is_compressible(self, data: bytes) -> bool:
        """
        Check if data contains compressible zero-byte sequences

        Args:
            data: Data bytes to check

        Returns:
            True if the data contains compressible sequences
        """
        if not data:
            return False
        
        # Count zero sequences
        i = 0
        while i < len(data):
            if data[i] == self.ZERO_BYTE:
                # Count consecutive zeros
                start = i
                while i < len(data) and data[i] == self.ZERO_BYTE:
                    i += 1
                
                sequence_length = i - start
                if sequence_length >= self.min_sequence_length:
                    return True
            else:
                i += 1
        
        return False 