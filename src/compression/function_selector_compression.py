"""
Function Selector Compression Module

This module implements techniques for compressing Ethereum function selectors
(the first 4 bytes of a transaction's calldata). Since many common functions
like ERC20 transfers are used frequently, we can replace 4-byte selectors with
1-byte indices to save 3 bytes per transaction.
"""

from typing import Dict, List, Tuple, Set, Optional, Union, Any
from collections import Counter
import json
import os


class FunctionSelectorCompressor:
    """
    Compresses Ethereum function selectors by replacing them with shorter indices.
    
    Techniques used:
    1. Dictionary-based compression: Replace 4-byte selectors with 1-byte indices
    2. Frequency analysis: Most common selectors get assigned indices
    """
    
    def __init__(self, max_selectors: int = 255):
        """
        Initialize the function selector compressor

        Args:
            max_selectors: Maximum number of selectors in the dictionary (default: 255)
                Limited by 1-byte index (0-255)
        """
        self.max_selectors = max_selectors
        
        # Dictionary of known selectors and their indices
        self.selector_dict: Dict[bytes, int] = {}
        
        # Counter for selector frequency
        self.selector_counter = Counter()
        
        # Reserved index for uncompressed data
        self.UNCOMPRESSED_MARKER = 0xFF
        
        # Statistics
        self.stats = {
            'total_selectors_processed': 0,
            'selectors_compressed': 0,
            'bytes_saved': 0,
            'dictionary_size': 0,
        }
    
    def build_dictionary(self, selectors: List[bytes]) -> None:
        """
        Build a selector dictionary from a list of function selectors
        Selectors are sorted by frequency to optimize compression

        Args:
            selectors: List of function selectors to build dictionary from
        """
        # Count selectors
        self.selector_counter.update(selectors)
        
        # Sort by frequency (most common first), reserve index 0xFF
        sorted_selectors = [selector for selector, _ in self.selector_counter.most_common(self.max_selectors - 1)]
        
        # Build dictionary (selector -> index)
        self.selector_dict = {selector: idx for idx, selector in enumerate(sorted_selectors)}
        
        # Update statistics
        self.stats['dictionary_size'] = len(self.selector_dict)
    
    def compress_selector(self, selector: bytes) -> Tuple[bytes, bool]:
        """
        Compress a function selector

        Args:
            selector: The 4-byte function selector to compress

        Returns:
            Tuple of (compressed_data, is_compressed)
        """
        # Validate selector
        if not selector or len(selector) != 4:
            # Invalid selector, return as is
            return selector, False
        
        # Update statistics
        self.stats['total_selectors_processed'] += 1
        
        # Check if selector is in dictionary
        if selector in self.selector_dict:
            index = self.selector_dict[selector]
            
            # Convert index to 1 byte
            compressed = bytes([index])
            
            # Update statistics
            self.stats['selectors_compressed'] += 1
            self.stats['bytes_saved'] += 3  # 4 bytes -> 1 byte
            
            return compressed, True
        else:
            # Selector not in dictionary, use UNCOMPRESSED_MARKER + original
            return bytes([self.UNCOMPRESSED_MARKER]) + selector, False
    
    def decompress_selector(self, data: bytes, is_compressed: bool) -> bytes:
        """
        Decompress a function selector

        Args:
            data: The compressed data
            is_compressed: Flag indicating if the selector is compressed

        Returns:
            The decompressed 4-byte selector
        """
        if not is_compressed:
            # Check if it has the uncompressed marker
            if data[0] == self.UNCOMPRESSED_MARKER:
                return data[1:5]  # Return the 4 bytes after the marker
            return data
        
        # Convert byte to index
        index = data[0]
        
        # Reverse lookup in dictionary
        reverse_dict = {idx: selector for selector, idx in self.selector_dict.items()}
        
        if index in reverse_dict:
            return reverse_dict[index]
        else:
            # This should not happen in practice
            raise ValueError(f"Function selector index {index} not found in dictionary")
    
    def compress_calldata(self, calldata: bytes) -> bytes:
        """
        Compress transaction calldata by replacing the function selector

        Args:
            calldata: Full calldata bytes

        Returns:
            Compressed calldata bytes
        """
        if len(calldata) < 4:
            # Not enough data for a selector
            return calldata
        
        # Extract selector (first 4 bytes)
        selector = calldata[:4]
        
        # Try to compress the selector
        compressed_selector, is_compressed = self.compress_selector(selector)
        
        if is_compressed:
            # Return compressed selector + rest of calldata
            return compressed_selector + calldata[4:]
        else:
            # Return marker + selector + rest of calldata
            return bytes([self.UNCOMPRESSED_MARKER]) + calldata
    
    def decompress_calldata(self, compressed_calldata: bytes) -> bytes:
        """
        Decompress transaction calldata

        Args:
            compressed_calldata: Compressed calldata bytes

        Returns:
            Decompressed calldata bytes
        """
        if not compressed_calldata:
            return compressed_calldata
        
        # Check the first byte
        first_byte = compressed_calldata[0]
        
        if first_byte == self.UNCOMPRESSED_MARKER:
            # Uncompressed marker, return the rest
            return compressed_calldata[1:]
        
        # Check if it's a compressed selector
        if first_byte in {idx for selector, idx in self.selector_dict.items()}:
            # Decompress the selector
            selector = self.decompress_selector(bytes([first_byte]), True)
            
            # Return decompressed selector + rest of calldata
            return selector + compressed_calldata[1:]
        
        # Not compressed or not recognized, return as is
        return compressed_calldata
    
    def save_dictionary(self, filepath: str) -> None:
        """
        Save the selector dictionary to a file

        Args:
            filepath: Path to save the dictionary
        """
        # Convert bytes keys to hex strings for JSON serialization
        serializable_dict = {
            selector.hex(): index for selector, index in self.selector_dict.items()
        }
        
        data = {
            'max_selectors': self.max_selectors,
            'dictionary': serializable_dict,
            'stats': self.stats
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_dictionary(self, filepath: str) -> None:
        """
        Load a selector dictionary from a file

        Args:
            filepath: Path to load the dictionary from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.max_selectors = data.get('max_selectors', self.max_selectors)
        
        # Convert hex strings back to bytes
        serialized_dict = data.get('dictionary', {})
        self.selector_dict = {
            bytes.fromhex(selector): index for selector, index in serialized_dict.items()
        }
        
        self.stats = data.get('stats', self.stats)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        # Calculate additional stats
        if self.stats['total_selectors_processed'] > 0:
            self.stats['compression_ratio'] = self.stats['selectors_compressed'] / self.stats['total_selectors_processed']
            self.stats['bytes_saved_per_selector'] = 3  # Always 3 bytes saved (4 -> 1)
        
        return self.stats
    
    def optimize_dictionary(self, selectors: List[bytes]) -> None:
        """
        Optimize the selector dictionary based on new data
        
        Args:
            selectors: New selectors to consider for the dictionary
        """
        # Update frequency counts
        self.selector_counter.update(selectors)
        
        # Rebuild dictionary based on updated frequencies
        self.build_dictionary(list(self.selector_counter.keys())) 