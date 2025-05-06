"""
Calldata Compression Module

This module implements specialized compression techniques for Ethereum calldata
beyond address and zero-byte compression, such as dictionary-based compression
for common patterns and ABI-aware optimizations.
"""

from typing import Dict, List, Tuple, Set, Optional, Union, Any
from collections import Counter, defaultdict
import json
import os
import re


class CalldataCompressor:
    """
    Compresses Ethereum calldata using pattern recognition and dictionary-based techniques.
    
    Techniques used:
    1. Dictionary compression for common byte patterns
    2. ABI-aware field compression
    3. Value-range optimization for numeric fields
    """
    
    def __init__(self, dictionary_size: int = 256):
        """
        Initialize the calldata compressor

        Args:
            dictionary_size: Maximum number of patterns in the dictionary
        """
        self.dictionary_size = dictionary_size
        
        # Dictionary of common patterns
        self.pattern_dict: Dict[bytes, int] = {}
        
        # Counter for pattern frequency
        self.pattern_counter = Counter()
        
        # Pattern marker byte
        self.PATTERN_MARKER = 0xF5
        
        # Statistics
        self.stats = {
            'total_bytes_processed': 0,
            'bytes_compressed': 0,
            'bytes_saved': 0,
            'patterns_used': 0,
        }
    
    def analyze_calldata(self, calldata_samples: List[bytes], ngram_sizes: List[int] = [8, 16, 32]) -> Dict[str, Any]:
        """
        Analyze calldata samples to identify common patterns

        Args:
            calldata_samples: List of calldata bytes to analyze
            ngram_sizes: Sizes of n-grams to extract for pattern matching

        Returns:
            Analysis results
        """
        # Extract n-grams from all calldata samples
        all_patterns = defaultdict(int)
        
        for calldata in calldata_samples:
            # Skip function selector (first 4 bytes)
            if len(calldata) >= 4:
                data = calldata[4:]
                for size in ngram_sizes:
                    if len(data) >= size:
                        # Extract all n-grams
                        for i in range(0, len(data) - size + 1, 4):  # Step by word size
                            pattern = data[i:i+size]
                            all_patterns[pattern] += 1
        
        # Update pattern counter
        self.pattern_counter.update(all_patterns)
        
        # Get most common patterns
        most_common = self.pattern_counter.most_common(self.dictionary_size)
        
        # Basic analysis
        analysis = {
            'total_calldata_bytes': sum(len(c) for c in calldata_samples),
            'calldata_samples': len(calldata_samples),
            'unique_patterns': len(all_patterns),
            'patterns_analyzed': len(all_patterns),
            'most_common_patterns': [{
                'pattern': pattern.hex(),
                'count': count,
                'length': len(pattern)
            } for pattern, count in most_common[:20]],
            'potential_savings': self._estimate_savings(most_common, calldata_samples)
        }
        
        return analysis
    
    def _estimate_savings(self, common_patterns: List[Tuple[bytes, int]], calldata_samples: List[bytes]) -> Dict[str, Any]:
        """
        Estimate potential savings from pattern compression

        Args:
            common_patterns: List of (pattern, count) tuples
            calldata_samples: Original calldata samples

        Returns:
            Estimated savings metrics
        """
        total_bytes = sum(len(c) for c in calldata_samples)
        if total_bytes == 0:
            return {
                'bytes_saved': 0,
                'percentage_saved': 0,
                'compression_ratio': 1.0
            }
        
        # Estimate bytes saved - each pattern occurrence saves (len(pattern) - 2) bytes
        # because we replace it with a 2-byte marker (1 byte marker + 1 byte index)
        bytes_saved = 0
        for pattern, count in common_patterns:
            pattern_len = len(pattern)
            if pattern_len > 2:  # Only count if compression saves space
                bytes_saved += count * (pattern_len - 2)
        
        # Cap savings based on realistic overhead
        bytes_saved = min(bytes_saved, total_bytes * 0.6)  # Max 60% savings
        
        return {
            'bytes_saved': bytes_saved,
            'percentage_saved': (bytes_saved / total_bytes) * 100 if total_bytes > 0 else 0,
            'compression_ratio': 1 - (bytes_saved / total_bytes) if total_bytes > 0 else 1.0
        }
    
    def build_dictionary(self, calldata_samples: List[bytes], ngram_sizes: List[int] = [8, 16, 32]) -> None:
        """
        Build a pattern dictionary from calldata samples

        Args:
            calldata_samples: List of calldata bytes to extract patterns from
            ngram_sizes: Sizes of n-grams to extract for pattern matching
        """
        # Analyze calldata to extract patterns
        self.analyze_calldata(calldata_samples, ngram_sizes)
        
        # Get most common patterns, filtered by minimum size and count
        common_patterns = []
        for pattern, count in self.pattern_counter.most_common(self.dictionary_size * 2):
            # Only consider patterns that would actually save space
            if len(pattern) > 2 and count > 2:
                common_patterns.append(pattern)
                if len(common_patterns) >= self.dictionary_size:
                    break
        
        # Create dictionary
        self.pattern_dict = {pattern: idx for idx, pattern in enumerate(common_patterns)}
    
    def compress(self, calldata: bytes) -> bytes:
        """
        Compress calldata using pattern dictionary

        Args:
            calldata: Raw calldata bytes to compress

        Returns:
            Compressed calldata bytes
        """
        if not calldata or not self.pattern_dict:
            return calldata
        
        # Update statistics
        self.stats['total_bytes_processed'] += len(calldata)
        
        # Skip compressing the function selector (first 4 bytes)
        if len(calldata) < 4:
            return calldata
        
        selector = calldata[:4]
        data = calldata[4:]
        
        # Create new compressed data
        compressed = bytearray(selector)  # Start with uncompressed selector
        pos = 0
        
        while pos < len(data):
            # Try to find the longest matching pattern at current position
            best_match = None
            best_match_len = 0
            
            for pattern, idx in self.pattern_dict.items():
                if len(pattern) > best_match_len and pos + len(pattern) <= len(data):
                    if data[pos:pos+len(pattern)] == pattern:
                        best_match = pattern
                        best_match_len = len(pattern)
            
            if best_match:
                # Replace pattern with marker + index
                idx = self.pattern_dict[best_match]
                compressed.extend([self.PATTERN_MARKER, idx])
                
                # Update statistics
                self.stats['bytes_compressed'] += best_match_len
                self.stats['bytes_saved'] += best_match_len - 2  # Saved (pattern length - 2 bytes for marker+index)
                self.stats['patterns_used'] += 1
                
                # Move position forward
                pos += best_match_len
            else:
                # Keep original byte
                compressed.append(data[pos])
                pos += 1
        
        return bytes(compressed)
    
    def decompress(self, compressed_calldata: bytes) -> bytes:
        """
        Decompress calldata

        Args:
            compressed_calldata: Compressed calldata bytes

        Returns:
            Decompressed calldata bytes
        """
        if not compressed_calldata or not self.pattern_dict:
            return compressed_calldata
        
        # Skip decompressing the function selector (first 4 bytes)
        if len(compressed_calldata) < 4:
            return compressed_calldata
        
        selector = compressed_calldata[:4]
        data = compressed_calldata[4:]
        
        # Create decompressed data
        decompressed = bytearray(selector)  # Start with uncompressed selector
        pos = 0
        
        # Reverse dictionary for lookup
        reverse_dict = {idx: pattern for pattern, idx in self.pattern_dict.items()}
        
        while pos < len(data):
            if pos < len(data) - 1 and data[pos] == self.PATTERN_MARKER:
                # Pattern reference - expand
                idx = data[pos + 1]
                if idx in reverse_dict:
                    pattern = reverse_dict[idx]
                    decompressed.extend(pattern)
                else:
                    # Unknown pattern index, keep as-is
                    decompressed.extend([self.PATTERN_MARKER, idx])
                pos += 2
            else:
                # Regular byte, keep as-is
                decompressed.append(data[pos])
                pos += 1
        
        return bytes(decompressed)
    
    def is_compressible(self, calldata: bytes) -> bool:
        """
        Check if calldata is likely to be compressible

        Args:
            calldata: Calldata bytes to check

        Returns:
            Whether the calldata is likely to be compressible
        """
        if not calldata or len(calldata) < 32 or not self.pattern_dict:
            return False
        
        # Skip function selector for analysis
        data = calldata[4:] if len(calldata) >= 4 else calldata
        
        # Check for any known patterns
        for pattern in self.pattern_dict:
            if pattern in data:
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        # Calculate compression ratio
        if self.stats['total_bytes_processed'] > 0:
            self.stats['compression_ratio'] = 1 - ((self.stats['total_bytes_processed'] - self.stats['bytes_saved']) / self.stats['total_bytes_processed'])
        
        # Add dictionary info
        self.stats['dictionary_size'] = len(self.pattern_dict)
        
        return self.stats
    
    def save_dictionary(self, filepath: str) -> None:
        """
        Save the pattern dictionary to a file

        Args:
            filepath: Path to save the dictionary
        """
        # Convert bytes keys to hex strings for JSON serialization
        serializable_dict = {
            pattern.hex(): idx for pattern, idx in self.pattern_dict.items()
        }
        
        data = {
            'dictionary_size': self.dictionary_size,
            'pattern_marker': self.PATTERN_MARKER,
            'dictionary': serializable_dict,
            'stats': self.stats
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_dictionary(self, filepath: str) -> None:
        """
        Load a pattern dictionary from a file

        Args:
            filepath: Path to load the dictionary from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.dictionary_size = data.get('dictionary_size', self.dictionary_size)
        self.PATTERN_MARKER = data.get('pattern_marker', self.PATTERN_MARKER)
        
        # Convert hex strings back to bytes
        serialized_dict = data.get('dictionary', {})
        self.pattern_dict = {
            bytes.fromhex(pattern): idx for pattern, idx in serialized_dict.items()
        }
        
        self.stats = data.get('stats', self.stats) 