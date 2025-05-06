"""
Address Compression Module

This module implements address compression techniques for Ethereum transactions.
The primary technique is to replace frequently used 20-byte addresses with shorter indices.
"""

from typing import Dict, List, Tuple, Set, Optional, Union, Any
from collections import Counter
import json
import os


class AddressCompressor:
    """
    Compresses Ethereum addresses by replacing them with shorter indices.
    
    Techniques used:
    1. Dictionary-based compression: Replace addresses with shorter indices
    2. Frequency-based ordering: Most common addresses get shortest indices
    3. Temporal locality optimization: Recent addresses get priority
    """
    
    def __init__(self, max_addresses: int = 65536, index_bytes: int = 2):
        """
        Initialize the address compressor

        Args:
            max_addresses: Maximum number of addresses in the dictionary (default: 65536)
            index_bytes: Number of bytes to use for address indices (default: 2)
                1 byte = 256 addresses
                2 bytes = 65536 addresses
                3 bytes = 16777216 addresses
        """
        self.max_addresses = max_addresses
        self.index_bytes = index_bytes
        
        # Dictionary of known addresses and their indices
        self.address_dict: Dict[str, int] = {}
        
        # Counter for address frequency
        self.address_counter = Counter()
        
        # Recently used addresses for temporal locality
        self.recent_addresses: List[str] = []
        self.max_recent = 1000
        
        # Statistics
        self.stats = {
            'total_addresses_processed': 0,
            'addresses_compressed': 0,
            'bytes_saved': 0,
            'dictionary_size': 0,
        }
    
    def build_dictionary(self, addresses: List[str]) -> None:
        """
        Build an address dictionary from a list of addresses
        Addresses are sorted by frequency to optimize compression

        Args:
            addresses: List of addresses to build dictionary from
        """
        # Count addresses
        self.address_counter.update(addresses)
        
        # Sort by frequency (most common first)
        sorted_addresses = [addr for addr, _ in self.address_counter.most_common(self.max_addresses)]
        
        # Build dictionary (address -> index)
        self.address_dict = {addr: idx for idx, addr in enumerate(sorted_addresses)}
        
        # Update statistics
        self.stats['dictionary_size'] = len(self.address_dict)
    
    def compress_address(self, address: str) -> Tuple[bytes, bool]:
        """
        Compress a single address

        Args:
            address: The address to compress

        Returns:
            Tuple of (compressed_data, is_compressed)
        """
        # Standardize address format
        if address:
            address = address.lower()
            if not address.startswith('0x'):
                address = '0x' + address
        else:
            # Handle null address
            return b'\x00' * self.index_bytes, True
        
        # Update statistics
        self.stats['total_addresses_processed'] += 1
        
        # Check if address is in dictionary
        if address in self.address_dict:
            index = self.address_dict[address]
            
            # Update recent addresses for temporal locality
            if address in self.recent_addresses:
                self.recent_addresses.remove(address)
            self.recent_addresses.insert(0, address)
            if len(self.recent_addresses) > self.max_recent:
                self.recent_addresses.pop()
            
            # Convert index to bytes with proper padding
            compressed = index.to_bytes(self.index_bytes, byteorder='big')
            
            # Update statistics
            self.stats['addresses_compressed'] += 1
            self.stats['bytes_saved'] += 20 - self.index_bytes
            
            return compressed, True
        else:
            # Address not in dictionary, return uncompressed
            # For actual implementation, we'd return the raw address bytes
            # But here we're just indicating it's not compressed
            return bytes.fromhex(address[2:]), False
    
    def decompress_address(self, data: bytes, is_compressed: bool) -> str:
        """
        Decompress address data

        Args:
            data: The compressed data
            is_compressed: Flag indicating if the data is compressed

        Returns:
            The decompressed address
        """
        if not is_compressed:
            # Convert raw bytes back to address string
            return '0x' + data.hex()
        
        # Convert bytes to index
        index = int.from_bytes(data, byteorder='big')
        
        # Reverse lookup in dictionary
        reverse_dict = {idx: addr for addr, idx in self.address_dict.items()}
        
        if index in reverse_dict:
            return reverse_dict[index]
        else:
            # This should not happen in practice
            raise ValueError(f"Address index {index} not found in dictionary")
    
    def compress_addresses_in_calldata(self, calldata: bytes) -> bytes:
        """
        Scan calldata for addresses and compress them

        This is a simplified implementation that demonstrates the approach.
        A complete implementation would need to be aware of the ABI structure.

        Args:
            calldata: Raw calldata bytes

        Returns:
            Compressed calldata bytes
        """
        # In a real implementation, we would need to parse the ABI
        # and understand where addresses are located in the calldata
        # For simplicity, we'll just scan for patterns that look like addresses
        
        # Placeholder for actual implementation
        return calldata
    
    def save_dictionary(self, filepath: str) -> None:
        """
        Save the address dictionary to a file

        Args:
            filepath: Path to save the dictionary
        """
        data = {
            'index_bytes': self.index_bytes,
            'max_addresses': self.max_addresses,
            'dictionary': self.address_dict,
            'stats': self.stats
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_dictionary(self, filepath: str) -> None:
        """
        Load an address dictionary from a file

        Args:
            filepath: Path to load the dictionary from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.index_bytes = data.get('index_bytes', self.index_bytes)
        self.max_addresses = data.get('max_addresses', self.max_addresses)
        self.address_dict = data.get('dictionary', {})
        self.stats = data.get('stats', self.stats)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        # Calculate compression ratio
        if self.stats['total_addresses_processed'] > 0:
            self.stats['compression_ratio'] = self.stats['addresses_compressed'] / self.stats['total_addresses_processed']
            self.stats['bytes_saved_per_address'] = self.stats['bytes_saved'] / self.stats['addresses_compressed'] if self.stats['addresses_compressed'] > 0 else 0
        
        return self.stats
    
    def optimize_dictionary(self) -> None:
        """
        Optimize the address dictionary based on usage patterns
        
        This reorders the dictionary to give frequently used and recent addresses
        smaller indices, which can further improve compression.
        """
        # Combine frequency and recency
        sorted_addresses = []
        
        # First add recent addresses
        for addr in self.recent_addresses:
            if addr not in sorted_addresses:
                sorted_addresses.append(addr)
        
        # Then add remaining addresses by frequency
        for addr, _ in self.address_counter.most_common():
            if addr not in sorted_addresses:
                sorted_addresses.append(addr)
        
        # Limit to max addresses
        sorted_addresses = sorted_addresses[:self.max_addresses]
        
        # Rebuild dictionary
        self.address_dict = {addr: idx for idx, addr in enumerate(sorted_addresses)}
        self.stats['dictionary_size'] = len(self.address_dict) 