"""
FunctionSelectorCompressor Adapter

This adapter implements the function selector compression technique
used in ZeroCompress.
"""

from typing import Dict, List, Tuple, Optional, Any


class FunctionSelectorCompressor:
    """
    Implementation of the function selector compression algorithm.
    
    This compressor maintains a dictionary of function selectors and their indices,
    allowing frequent selectors to be represented by a single byte index.
    """
    
    def __init__(self, max_selectors: int = 255):
        """
        Initialize the function selector compressor
        
        Args:
            max_selectors: Maximum number of selectors in the dictionary (max 255)
        """
        self.max_selectors = min(max_selectors, 255)  # Ensure we don't exceed single byte
        
        # Selector dictionary: maps selectors to indices
        self.selector_dict: Dict[bytes, int] = {}
        # Reverse dictionary for decompression
        self.reverse_dict: Dict[int, bytes] = {}
        
        # Marker for uncompressed selectors
        self.UNCOMPRESSED_MARKER = 0xFF
        
        # Stats
        self.stats = {
            'total_selectors_processed': 0,
            'selectors_compressed': 0,
            'bytes_saved': 0,
            'dictionary_size': 0,
        }
        
        # Initialize with common selectors
        self._init_common_selectors()
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress transaction data by replacing known function selectors with indices
        
        Args:
            data: Transaction data bytes
            
        Returns:
            Compressed data bytes
        """
        if not data or len(data) < 4 or not self.selector_dict:
            return data
        
        # Extract selector (first 4 bytes)
        selector = data[:4]
        rest_of_data = data[4:]
        
        # Try to compress the selector
        compressed_selector, is_compressed = self.compress_selector(selector)
        
        if is_compressed:
            # Selector was compressed
            self.stats['selectors_compressed'] += 1
            self.stats['bytes_saved'] += 4 - len(compressed_selector)
            return compressed_selector + rest_of_data
        else:
            # Selector not in dictionary, return original
            return data
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data containing compressed function selectors
        
        Args:
            data: Compressed data bytes
            
        Returns:
            Decompressed data bytes
        """
        if not data or not self.reverse_dict:
            return data
        
        # Check first byte
        first_byte = data[0]
        
        if first_byte in self.reverse_dict:
            # This is a compressed selector
            selector = self.reverse_dict[first_byte]
            return selector + data[1:]
        elif first_byte == self.UNCOMPRESSED_MARKER and len(data) >= 5:
            # Uncompressed marker + original selector
            return data[1:]
        else:
            # Not compressed or invalid
            return data
    
    def compress_selector(self, selector: bytes) -> Tuple[bytes, bool]:
        """
        Compress a single function selector
        
        Args:
            selector: Function selector (4 bytes)
            
        Returns:
            Tuple of (compressed_bytes, is_compressed)
        """
        # Track stats
        self.stats['total_selectors_processed'] += 1
        
        if len(selector) != 4:
            return selector, False
        
        if selector in self.selector_dict:
            # Selector is in dictionary
            index = self.selector_dict[selector]
            return bytes([index]), True
        else:
            # Not in dictionary
            # In production, we'd use a marker to indicate uncompressed selectors
            # return bytes([self.UNCOMPRESSED_MARKER]) + selector, False
            return selector, False
    
    def decompress_selector(self, compressed: bytes, is_index: bool = False) -> bytes:
        """
        Decompress a compressed function selector
        
        Args:
            compressed: Compressed selector bytes
            is_index: Whether the input is an index or marker+selector
            
        Returns:
            Original selector (4 bytes)
        """
        if is_index and len(compressed) == 1:
            index = compressed[0]
            if index in self.reverse_dict:
                return self.reverse_dict[index]
        
        if not is_index and len(compressed) >= 5 and compressed[0] == self.UNCOMPRESSED_MARKER:
            # Uncompressed marker + original selector
            return compressed[1:5]
        
        # Unable to decompress
        return compressed
    
    def build_dictionary(self, selectors: List[bytes]) -> None:
        """
        Build the selector dictionary from a list of selectors
        
        Args:
            selectors: List of function selectors (4 bytes each)
        """
        # Reset dictionary
        self.selector_dict = {}
        self.reverse_dict = {}
        
        # Filter valid selectors
        valid_selectors = [s for s in selectors if len(s) == 4]
        
        # Sort by frequency or use a predefined set for common functions
        # For this demo, we'll just use the first max_selectors
        for i, selector in enumerate(valid_selectors[:self.max_selectors]):
            if i >= 255:
                break  # Can't represent more than 255 selectors with a single byte
            
            self.selector_dict[selector] = i
            self.reverse_dict[i] = selector
        
        self.stats['dictionary_size'] = len(self.selector_dict)
    
    def _init_common_selectors(self) -> None:
        """Initialize dictionary with common Ethereum function selectors"""
        # Top ERC20 methods
        common_selectors = {
            # ERC20 methods
            bytes.fromhex('a9059cbb'): 0,  # transfer(address,uint256)
            bytes.fromhex('095ea7b3'): 1,  # approve(address,uint256)
            bytes.fromhex('23b872dd'): 2,  # transferFrom(address,address,uint256)
            bytes.fromhex('70a08231'): 3,  # balanceOf(address)
            bytes.fromhex('dd62ed3e'): 4,  # allowance(address,address)
            bytes.fromhex('18160ddd'): 5,  # totalSupply()
            bytes.fromhex('a457c2d7'): 6,  # decreaseAllowance(address,uint256)
            bytes.fromhex('39509351'): 7,  # increaseAllowance(address,uint256)
            
            # Common UniswapV2/V3 methods
            bytes.fromhex('022c0d9f'): 8,  # swap
            bytes.fromhex('38ed1739'): 9,  # swapExactTokensForTokens
            bytes.fromhex('7ff36ab5'): 10, # swapExactETHForTokens
            bytes.fromhex('4a25d94a'): 11, # swapTokensForExactETH
            bytes.fromhex('18cbafe5'): 12, # swapExactTokensForETH
            bytes.fromhex('fb3bdb41'): 13, # swapETHForExactTokens
            bytes.fromhex('5c11d795'): 14, # swapExactTokensForTokensSupportingFeeOnTransferTokens
            
            # Some multisig methods
            bytes.fromhex('c01a8c84'): 15, # confirmTransaction
            bytes.fromhex('ee22610b'): 16, # executeTransaction
            bytes.fromhex('20ea8d86'): 17, # revokeConfirmation
            bytes.fromhex('c6427474'): 18, # submitTransaction
            
            # Staking/farming methods
            bytes.fromhex('a694fc3a'): 19, # stake
            bytes.fromhex('3d18b912'): 20, # getReward
            bytes.fromhex('e9fad8ee'): 21, # exit
            bytes.fromhex('2e1a7d4d'): 22, # withdraw
            
            # Some more common methods
            bytes.fromhex('a0712d68'): 23, # mint
            bytes.fromhex('42966c68'): 24, # burn
            bytes.fromhex('fe9d9303'): 25, # claim
            bytes.fromhex('2f54bf6e'): 26, # isOwner
            bytes.fromhex('8da5cb5b'): 27, # owner
            bytes.fromhex('715018a6'): 28, # renounceOwnership
            bytes.fromhex('f2fde38b'): 29, # transferOwnership
        }
        
        # Add to dictionary
        self.selector_dict = common_selectors
        # Create reverse dictionary
        self.reverse_dict = {idx: selector for selector, idx in common_selectors.items()}
        
        self.stats['dictionary_size'] = len(self.selector_dict)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return self.stats 