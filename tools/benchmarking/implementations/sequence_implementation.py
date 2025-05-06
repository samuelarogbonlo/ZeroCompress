#!/usr/bin/env python3
"""
Sequence-CZIP Reference Implementation

This module provides a simplified implementation of Sequence.xyz's CZIP compression
algorithm, based on their public documentation and research. This is used for
benchmarking comparison with ZeroCompress.

Note: This is not an official Sequence implementation but a reference model for
benchmarking purposes only.
"""

import zlib
import struct
from typing import Dict, List, Tuple, Set, Optional, Union, Any, ByteString
import binascii


class SequenceCompressor:
    """
    Reference implementation of Sequence.xyz's CZIP compression technique
    
    Based on public information, Sequence's compression consists of:
    1. Address dictionary compression
    2. Zero-byte run-length encoding
    3. Common pattern optimizations
    
    This is a simplified model for benchmarking purposes.
    """
    
    # Common EVM function selectors
    COMMON_SELECTORS = {
        b"\xa9\x05\x9c\xbb": 0,  # transfer(address,uint256)
        b"\x09\x5e\xa7\xb3": 1,  # approve(address,uint256)
        b"\x23\xb8\x72\xdd": 2,  # transferFrom(address,address,uint256)
        b"\x70\xa0\x82\x31": 3,  # balanceOf(address)
        b"\xdd\x62\xed\x3e": 4,  # allowance(address,address)
        b"\x18\x16\x0d\xdd": 5,  # totalSupply()
        b"\x31\x34\xe8\xa2": 6,  # mint(address,uint256)
        b"\x42\x84\x2e\x0e": 7,  # burn(address,uint256)
        b"\x09\x5e\xa7\xb3": 8,  # approve(address,uint256)
        b"\x31\x34\xe8\xa2": 9,  # mint(address,uint256)
    }
    
    def __init__(self):
        """Initialize the Sequence CZIP compressor"""
        self.address_dict = {}  # Address -> index mapping
        self.next_addr_index = 0
        self.reset_frequency = 1000  # Reset dictionary after this many compressions
        self.compression_count = 0
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress transaction data using Sequence-CZIP technique
        
        Args:
            data: Raw transaction data bytes
            
        Returns:
            Compressed data bytes
        """
        self.compression_count += 1
        
        # Reset dictionary periodically to simulate Sequence's behavior
        if self.compression_count % self.reset_frequency == 0:
            self.address_dict = {}
            self.next_addr_index = 0
        
        # 1. Extract function selector if present (first 4 bytes)
        if len(data) >= 4:
            selector = data[:4]
            remaining = data[4:]
        else:
            selector = b''
            remaining = data
        
        # 2. Compress selector if it's common
        if selector in self.COMMON_SELECTORS:
            compressed_selector = bytes([0xC0 | self.COMMON_SELECTORS[selector]])
        else:
            compressed_selector = selector
        
        # 3. Find and compress addresses in the data
        compressed_data = bytearray()
        i = 0
        
        while i < len(remaining):
            # Check if we have a potential 20-byte address
            if i + 20 <= len(remaining):
                potential_addr = remaining[i:i+20]
                
                # Heuristic: Addresses often follow certain patterns
                if self._is_likely_address(potential_addr):
                    # Compress the address
                    if potential_addr in self.address_dict:
                        index = self.address_dict[potential_addr]
                    else:
                        index = self.next_addr_index
                        self.address_dict[potential_addr] = index
                        self.next_addr_index += 1
                    
                    # Add compressed address (0xA0 marker + index)
                    compressed_data.append(0xA0 | (index >> 8))
                    compressed_data.append(index & 0xFF)
                    i += 20
                    continue
            
            # 4. RLE for zero bytes
            if remaining[i] == 0:
                # Count consecutive zeros
                zero_count = 1
                j = i + 1
                while j < len(remaining) and remaining[j] == 0 and zero_count < 31:
                    zero_count += 1
                    j += 1
                
                if zero_count > 1:
                    # Encode zero sequence (0xE0 marker + count)
                    compressed_data.append(0xE0 | zero_count)
                    i += zero_count
                    continue
            
            # 5. Pass through regular byte
            compressed_data.append(remaining[i])
            i += 1
        
        # Combine components
        result = compressed_selector + bytes(compressed_data)
        
        # 6. If compression didn't help, return original with marker
        if len(result) >= len(data):
            return b'\xFF' + data
        
        # 7. Add compression marker and return
        return b'\xFE' + result
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """
        Decompress data that was compressed with Sequence-CZIP technique
        
        Args:
            compressed_data: Compressed data bytes
            
        Returns:
            Original transaction data bytes
        """
        if not compressed_data:
            return b''
        
        # Check compression marker
        marker = compressed_data[0]
        data = compressed_data[1:]
        
        # If uncompressed marker, return original
        if marker == 0xFF:
            return data
        
        # If not our compression marker, return as is
        if marker != 0xFE:
            return compressed_data
        
        # Initialize decompression structures
        decompressed = bytearray()
        addr_lookup = {}  # Index -> address mapping
        
        # Process function selector
        if data and (data[0] & 0xF0) == 0xC0:
            # Decompress common selector
            selector_index = data[0] & 0x0F
            for sel, idx in self.COMMON_SELECTORS.items():
                if idx == selector_index:
                    decompressed.extend(sel)
                    data = data[1:]
                    break
        
        # Process the rest of the data
        i = 0
        while i < len(data):
            # Check for address reference (0xA0 marker)
            if (data[i] & 0xF0) == 0xA0 and i + 1 < len(data):
                # Get address index
                index = ((data[i] & 0x0F) << 8) | data[i+1]
                
                if index in addr_lookup:
                    # Use address from lookup
                    decompressed.extend(addr_lookup[index])
                else:
                    # If address not in lookup, use placeholder
                    # (In a real implementation this would be an error)
                    placeholder = bytes([0xFF] * 20)
                    decompressed.extend(placeholder)
                    addr_lookup[index] = placeholder
                
                i += 2
                continue
            
            # Check for zero sequence (0xE0 marker)
            if (data[i] & 0xF0) == 0xE0:
                zero_count = data[i] & 0x1F
                decompressed.extend(bytes([0] * zero_count))
                i += 1
                continue
            
            # Regular byte
            decompressed.append(data[i])
            
            # Check if we just added a potential address
            if len(decompressed) >= 20:
                potential_addr = bytes(decompressed[-20:])
                if self._is_likely_address(potential_addr):
                    # Record this address for future reference
                    found = False
                    for idx, addr in addr_lookup.items():
                        if addr == potential_addr:
                            found = True
                            break
                    
                    if not found and len(addr_lookup) < 4096:  # Max dictionary size
                        next_idx = len(addr_lookup)
                        addr_lookup[next_idx] = potential_addr
            
            i += 1
        
        return bytes(decompressed)
    
    def _is_likely_address(self, data: bytes) -> bool:
        """
        Heuristic to determine if a 20-byte sequence is likely an address
        
        This is a simplified version of Sequence's heuristic, which likely
        has more sophisticated detection.
        """
        # Check leading zeros (common in addresses)
        if data.startswith(b'\x00\x00'):
            return True
        
        # Check for typical contract address patterns
        if 0x20 <= data[0] <= 0x9F and sum(data[1:4]) < 0x10:
            return True
        
        # EOA addresses often have statistical patterns
        zero_count = data.count(0)
        if zero_count >= 5:  # Addresses often have several zero bytes
            return True
        
        # By default, assume not an address to avoid false positives
        return False 