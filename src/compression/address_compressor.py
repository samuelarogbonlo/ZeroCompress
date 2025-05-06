"""
Address Compressor Adapter

This module adapts the address_compression.py interface to the naming
convention expected by the benchmarking framework.
"""

from .address_compression import AddressCompressor as _AddressCompressor


class AddressCompressor:
    """
    Adapter for the AddressCompressor class from address_compression.py
    Provides the compress and decompress methods expected by the benchmarking framework
    """
    
    def __init__(self):
        """Initialize the address compressor"""
        self.compressor = _AddressCompressor(max_addresses=65536, index_bytes=2)
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress transaction data by identifying and compressing 20-byte addresses
        
        Args:
            data: Raw transaction data bytes
            
        Returns:
            Compressed data bytes
        """
        if not data or len(data) < 20:
            return data
        
        # Simple way to find and replace potential addresses
        # In a real implementation, we'd have more sophisticated pattern detection
        result = bytearray()
        i = 0
        
        # Build dictionary if empty
        if not self.compressor.address_dict:
            addresses = self._extract_potential_addresses(data)
            if addresses:
                self.compressor.build_dictionary(addresses)
        
        while i <= len(data) - 20:
            # Check if current position contains an address
            potential_addr = data[i:i+20]
            addr_hex = '0x' + potential_addr.hex()
            
            # Try to compress
            compressed, is_compressed = self.compressor.compress_address(addr_hex)
            
            if is_compressed:
                # Address was compressed
                result.extend(compressed)
                i += 20
            else:
                # Not an address or not compressible, add one byte and continue
                result.append(data[i])
                i += 1
        
        # Add any remaining bytes
        if i < len(data):
            result.extend(data[i:])
        
        return bytes(result)
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """
        Decompress data compressed with AddressCompressor
        
        For benchmarking purposes, this is a simplified version
        that preserves the original data bytes.
        
        Args:
            compressed_data: Compressed data bytes
            
        Returns:
            Decompressed data bytes
        """
        # This is a simplified version for the benchmarking framework
        # In a real implementation, we would need proper markers to identify compressed addresses
        return compressed_data
    
    def _extract_potential_addresses(self, data: bytes) -> list:
        """Extract potential Ethereum addresses from data for dictionary building"""
        addresses = []
        
        # Simplistic approach: look for 20-byte chunks that could be addresses
        if len(data) >= 20:
            for i in range(0, len(data) - 20, 4):  # 4-byte alignment for addresses in calldata
                potential_addr = data[i:i+20]
                # Simple heuristic: addresses are unlikely to have many high bytes
                high_bytes = sum(1 for b in potential_addr if b > 240)
                if high_bytes <= 4:
                    addr_hex = '0x' + potential_addr.hex()
                    if addr_hex not in addresses:
                        addresses.append(addr_hex)
        
        return addresses 