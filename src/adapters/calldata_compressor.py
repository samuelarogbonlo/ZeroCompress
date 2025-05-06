"""
CalldataCompressor Adapter

This adapter implements the calldata pattern compression technique
used in ZeroCompress.
"""

from typing import Dict, List, Tuple, Optional, Any
import struct


class CalldataCompressor:
    """
    Implementation of calldata pattern compression algorithm.
    
    This compressor identifies common patterns in calldata and replaces them
    with shorter references to a pattern dictionary.
    """
    
    def __init__(self, dictionary_size: int = 256):
        """
        Initialize the calldata pattern compressor
        
        Args:
            dictionary_size: Maximum number of patterns in the dictionary
        """
        self.dictionary_size = min(dictionary_size, 256)  # Maximum 256 patterns for single-byte index
        
        # Pattern dictionary: maps patterns to indices
        self.pattern_dict: Dict[bytes, int] = {}
        # Reverse dictionary for decompression
        self.reverse_dict: Dict[int, bytes] = {}
        
        # Compression configuration
        self.MIN_PATTERN_LENGTH = 4  # Minimum bytes for pattern to be worth compressing
        self.PATTERN_MARKER = 0xFE   # Marker to indicate compressed pattern
        
        # Statistics
        self.stats = {
            'total_bytes_processed': 0,
            'total_bytes_compressed': 0,
            'patterns_replaced': 0,
            'bytes_saved': 0,
            'dictionary_size': 0,
        }
        
        # Initialize with common patterns
        self._init_common_patterns()
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress calldata by replacing common patterns with references
        
        Args:
            data: Calldata bytes
            
        Returns:
            Compressed data bytes
        """
        if not data or not self.pattern_dict:
            return data
        
        # Update statistics
        self.stats['total_bytes_processed'] += len(data)
        
        result = bytearray()
        i = 0
        
        while i < len(data):
            longest_match = b''
            longest_match_index = -1
            
            # Find the longest pattern match starting at current position
            for pattern, index in self.pattern_dict.items():
                pattern_len = len(pattern)
                
                if (i + pattern_len <= len(data) and 
                    pattern_len >= self.MIN_PATTERN_LENGTH and
                    data[i:i+pattern_len] == pattern):
                    
                    if pattern_len > len(longest_match):
                        longest_match = pattern
                        longest_match_index = index
            
            if longest_match:
                # We found a pattern match
                # Add marker + index to result
                result.extend(bytes([self.PATTERN_MARKER, longest_match_index]))
                
                # Move index past the pattern
                i += len(longest_match)
                
                # Update statistics
                self.stats['patterns_replaced'] += 1
                self.stats['bytes_saved'] += len(longest_match) - 2  # 2 bytes for marker + index
            else:
                # No pattern match, copy the byte
                result.append(data[i])
                i += 1
        
        compressed_data = bytes(result)
        self.stats['total_bytes_compressed'] += len(compressed_data)
        
        return compressed_data
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress calldata with pattern references
        
        Args:
            data: Compressed data bytes
            
        Returns:
            Decompressed data bytes
        """
        if not data or not self.reverse_dict:
            return data
        
        result = bytearray()
        i = 0
        
        while i < len(data):
            # Check for pattern marker
            if i + 1 < len(data) and data[i] == self.PATTERN_MARKER:
                # Get pattern index
                pattern_index = data[i+1]
                
                if pattern_index in self.reverse_dict:
                    # Replace with the pattern
                    pattern = self.reverse_dict[pattern_index]
                    result.extend(pattern)
                else:
                    # Unknown pattern index, keep as is
                    result.append(data[i])
                    result.append(data[i+1])
                
                i += 2  # Skip marker and index
            else:
                # Not a pattern, copy the byte
                result.append(data[i])
                i += 1
        
        return bytes(result)
    
    def build_dictionary(self, data_samples: List[bytes]) -> None:
        """
        Build pattern dictionary from sample calldata
        
        Args:
            data_samples: List of sample calldata bytes
        """
        # Reset dictionary
        self.pattern_dict = {}
        self.reverse_dict = {}
        
        # For this demo, we'll use a simple frequency-based approach
        # In production, this would use more sophisticated pattern detection
        
        # Count pattern occurrences
        pattern_counts = {}
        
        for data in data_samples:
            # Look for patterns of different lengths
            for pattern_len in range(self.MIN_PATTERN_LENGTH, 33):  # Up to 32 bytes (common in Ethereum)
                for i in range(len(data) - pattern_len + 1):
                    pattern = data[i:i+pattern_len]
                    
                    if pattern not in pattern_counts:
                        pattern_counts[pattern] = 0
                    
                    pattern_counts[pattern] += 1
        
        # Sort patterns by frequency * length (to prioritize longer patterns)
        sorted_patterns = sorted(
            pattern_counts.items(),
            key=lambda x: x[1] * len(x[0]),
            reverse=True
        )
        
        # Take top patterns up to dictionary size
        for i, (pattern, _) in enumerate(sorted_patterns[:self.dictionary_size]):
            if i >= 256:  # Single byte index limitation
                break
                
            self.pattern_dict[pattern] = i
            self.reverse_dict[i] = pattern
        
        self.stats['dictionary_size'] = len(self.pattern_dict)
    
    def _init_common_patterns(self) -> None:
        """Initialize with common Ethereum calldata patterns"""
        common_patterns = {
            # Common uint256 values
            bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000000'): 0,  # 0
            bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000001'): 1,  # 1
            bytes.fromhex('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'): 2,  # max uint256
            
            # Common address padding (address: uint256)
            bytes.fromhex('000000000000000000000000'): 3,
            
            # ERC20 Transfer function args structure (minus the address)
            bytes.fromhex('0000000000000000000000000000000000000000000000'): 4,
            
            # ERC20 typical amount (0.01 ETH in wei)
            bytes.fromhex('00000000000000000000000000000000000000000000000002386f26fc10000'): 5,
            
            # ERC20 typical amount (0.1 ETH in wei)
            bytes.fromhex('0000000000000000000000000000000000000000000000000de0b6b3a7640000'): 6,
            
            # ERC20 typical amount (1 ETH in wei)
            bytes.fromhex('000000000000000000000000000000000000000000000000d8d726b7177a8000'): 7,
            
            # Uniswap deadline (max uint)
            bytes.fromhex('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'): 8,
            
            # ERC20 max approval
            bytes.fromhex('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'): 9,
            
            # Zeros (common padding)
            bytes.fromhex('00000000'): 10,
            bytes.fromhex('000000000000'): 11,
            bytes.fromhex('00000000000000000000'): 12,
            
            # Bool true padded
            bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000001'): 13,
            
            # Bool false padded
            bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000000'): 14,
        }
        
        # Add to dictionary
        self.pattern_dict = common_patterns
        # Create reverse dictionary
        self.reverse_dict = {idx: pattern for pattern, idx in common_patterns.items()}
        
        self.stats['dictionary_size'] = len(self.pattern_dict)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        # Calculate overall compression ratio if data was processed
        if self.stats['total_bytes_processed'] > 0:
            ratio = 1 - (self.stats['total_bytes_compressed'] / self.stats['total_bytes_processed'])
            self.stats['compression_ratio'] = ratio
        
        return self.stats 