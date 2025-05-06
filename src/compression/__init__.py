"""
ZeroCompress Compression Library

This package provides specialized compression techniques for Ethereum calldata
optimized for L2 rollups.
"""

__version__ = '0.1.0'

from .compressor import ZeroCompressor
from .address_compression import AddressCompressor
from .zero_byte_compression import ZeroByteCompressor
from .function_selector_compression import FunctionSelectorCompressor
from .calldata_compression import CalldataCompressor 