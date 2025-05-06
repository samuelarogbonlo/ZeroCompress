"""
AddressCompressor Adapter

This adapter implements the Ethereum address compression technique
used in ZeroCompress.
"""

from typing import Dict, List, Tuple, Optional, Any
import struct


class AddressCompressor:
    """
    Implementation of the address compression algorithm.
    
    This compressor maintains a dictionary of addresses and their indices,
    allowing frequent addresses to be represented by a small index.
    """
    
    def __init__(self, max_addresses: int = 65536, index_bytes: int = 2):
        """
        Initialize the address compressor
        
        Args:
            max_addresses: Maximum number of addresses in the dictionary
            index_bytes: Number of bytes to use for the address index
        """
        self.max_addresses = max_addresses
        self.index_bytes = index_bytes  # Usually 1 or 2 bytes
        
        # Address dictionary: maps addresses to indices
        self.address_dict: Dict[str, int] = {}
        # Reverse dictionary for decompression
        self.reverse_dict: Dict[int, str] = {}
        
        # Marker for uncompressed addresses
        self.UNCOMPRESSED_MARKER = 0xFF
        
        # Statistics
        self.stats = {
            'total_addresses_processed': 0,
            'addresses_compressed': 0,
            'bytes_saved': 0,
            'dictionary_size': 0,
        }
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress transaction data by replacing known addresses with indices
        
        Args:
            data: Transaction data bytes
            
        Returns:
            Compressed data bytes
        """
        if not data or len(data) < 20 or not self.address_dict:
            return data
        
        result = bytearray()
        i = 0
        
        # Process data in 20-byte chunks (potential addresses)
        while i <= len(data) - 20:
            potential_addr = data[i:i+20]
            addr_hex = '0x' + potential_addr.hex()
            
            compressed, is_compressed = self.compress_address(addr_hex)
            
            if is_compressed:
                # Address was compressed
                result.extend(compressed)
                i += 20
                self.stats['addresses_compressed'] += 1
                self.stats['bytes_saved'] += 20 - len(compressed)
            else:
                # Not an address or not in dictionary
                result.append(data[i])
                i += 1
        
        # Add any remaining bytes
        if i < len(data):
            result.extend(data[i:])
        
        return bytes(result)
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data containing compressed addresses
        
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
            # Check if this could be a compressed address marker
            if i + self.index_bytes < len(data):
                marker = data[i]
                
                if marker == self.UNCOMPRESSED_MARKER and i + 21 <= len(data):
                    # Uncompressed address marker + address (20 bytes)
                    result.extend(data[i+1:i+21])
                    i += 21
                    continue
                
                # Try to read index based on index_bytes
                if self.index_bytes == 1:
                    idx = marker
                else:  # index_bytes == 2
                    idx = (marker << 8) | data[i+1]
                
                # Check if it's a valid index
                if idx in self.reverse_dict:
                    # Decompress the address
                    addr_hex = self.reverse_dict[idx]
                    addr_bytes = bytes.fromhex(addr_hex[2:])  # Remove '0x' prefix
                    result.extend(addr_bytes)
                    i += self.index_bytes
                    continue
            
            # Not a compressed address, add one byte and continue
            result.append(data[i])
            i += 1
        
        return bytes(result)
    
    def compress_address(self, address: str) -> Tuple[bytes, bool]:
        """
        Compress a single Ethereum address
        
        Args:
            address: Ethereum address as hex string (with 0x prefix)
            
        Returns:
            Tuple of (compressed_bytes, is_compressed)
        """
        # Track stats
        self.stats['total_addresses_processed'] += 1
        
        if not address.startswith('0x') or len(address) != 42:
            # Not a valid Ethereum address
            return bytes.fromhex(address[2:]) if address.startswith('0x') else bytes.fromhex(address), False
        
        address = address.lower()  # Normalize
        
        if address in self.address_dict:
            # Address is in the dictionary
            index = self.address_dict[address]
            
            if self.index_bytes == 1:
                return bytes([index]), True
            else:  # index_bytes == 2
                # Big-endian encoding
                return struct.pack('>H', index), True
        else:
            # Not in dictionary - return the original with marker in production
            # For simplicity in this demo, we just return the original address
            addr_bytes = bytes.fromhex(address[2:])
            
            # If this were a production system, we'd use a marker to indicate 
            # uncompressed addresses for proper decompression:
            # return bytes([self.UNCOMPRESSED_MARKER]) + addr_bytes, False
            
            return addr_bytes, False
    
    def build_dictionary(self, addresses: List[str]) -> None:
        """
        Build the address dictionary from a list of addresses
        
        Args:
            addresses: List of Ethereum addresses
        """
        # Reset dictionary
        self.address_dict = {}
        self.reverse_dict = {}
        
        # Normalize addresses
        normalized = [addr.lower() for addr in addresses if addr.startswith('0x') and len(addr) == 42]
        
        # Sort by frequency or use a predefined set for common contracts
        # For this demo, we'll just use the first max_addresses
        for i, addr in enumerate(normalized[:self.max_addresses]):
            if i >= 2**16 and self.index_bytes == 2:
                break  # Can't represent more than 2^16 addresses with 2 bytes
            elif i >= 2**8 and self.index_bytes == 1:
                break  # Can't represent more than 2^8 addresses with 1 byte
            
            self.address_dict[addr] = i
            self.reverse_dict[i] = addr
        
        self.stats['dictionary_size'] = len(self.address_dict)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return self.stats 