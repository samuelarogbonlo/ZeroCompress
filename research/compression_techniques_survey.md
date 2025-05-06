# ZeroCompress: Survey of Existing Compression Techniques

## Introduction

This document provides a comprehensive review of existing compression techniques for Ethereum rollup data, focusing on approaches that have been theoretically described or practically implemented.

## Sources

1. Vitalik Buterin's Research:
   - [Rollup-Centric Ethereum Roadmap](http://vitalik.eth.limo/general/2021/01/05/rollup.html)
   - [Future Directions for Ethereum](https://vitalik.eth.limo/general/2024/10/17/futures2.html)

2. Production Implementations:
   - [Sequence.xyz's Calldata Compression](https://sequence.xyz/blog/compressing-calldata)
   - [ScopeLift's L2-optimizoooors](https://github.com/ScopeLift/l2-optimizoooors)
   - [BLS Wallet](https://github.com/getwax/bls-wallet)

## Compression Techniques

### 1. Zero-byte Elimination

**Description:** Replace long sequences of zero bytes with a compact representation indicating the number of zeros.

**Technical Details:**
- Implementation uses two bytes to represent the count of consecutive zero bytes
- Particularly effective for sparse data structures and padding

**Real-world Impact:**
- Sequence.xyz implementation demonstrates significant savings on this simple technique alone
- Most effective on calldata with many zero bytes (common in Ethereum transactions)

**Example:**
```
Original:   0x0000000000000000000000000000000000000000 (20 bytes)
Compressed: 0x00 0x14 (2 bytes, representing 20 zeros)
```

### 2. Address Compression

**Description:** Replace frequently used 20-byte Ethereum addresses with shorter indices/pointers to previously seen addresses.

**Technical Details:**
- Addresses typically occupy 20 bytes each
- Can be replaced with 2-4 byte pointers to historical addresses
- Requires maintaining a dictionary/mapping of addresses

**Real-world Impact:**
- Sequence.xyz reports substantial savings when transactions reuse the same addresses
- Particularly effective for contract interactions where the same contracts are called repeatedly

**Example:**
```
Original:   0x912ce59144191c1204e64559fe8253a0e49e6548 (20 bytes)
Compressed: 0x0001 (2 bytes, pointing to address index 1 in history)
```

### 3. Transaction Value Serialization

**Description:** Custom encoding for common transaction values (ETH amounts, gas values) that are typically represented inefficiently.

**Technical Details:**
- Most transaction values have very few significant digits
- Example: 0.25 ETH = 250,000,000,000,000,000 wei (requires many bytes in standard encoding)
- Can be represented using custom decimal floating point format or dictionary of common values

**Real-world Impact:**
- Sequence.xyz implementation confirms significant savings for common values
- For common approval values (like max uint256 for token approvals), savings can reach ~50%

**Example:**
```
Original:   0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff (32 bytes)
Compressed: 0xFE (1-2 bytes, special code for max uint256)
```

### 4. BLS Signature Aggregation

**Description:** Replace multiple ECDSA signatures with a single aggregated BLS signature.

**Technical Details:**
- BLS signatures can be mathematically combined
- Multiple transaction signatures can be verified with a single verification operation
- Significantly reduces signature data size for batched transactions

**Implementation Status:**
- Used in Ethereum consensus layer
- BLS Wallet implements through ERC-4337
- Not yet widely deployed in rollups due to computational overhead and compatibility concerns

**Challenges:**
- Higher computational costs for verification
- Reduced compatibility with hardware security modules
- Requires protocol changes or adoption of standards like ERC-4337

### 5. State Diff Compression (ZK Rollups)

**Description:** Instead of publishing complete transactions, publish compressed state differences.

**Technical Details:**
- ZK rollups can prove state transitions without revealing full transaction data
- Only state differences need to be published
- Can be further compressed using specialized encodings

**Trade-offs:**
- Reduces auditability (transaction details not fully available)
- Breaks compatibility with block explorers and analytics tools
- May require specialized client software

## Quantitative Results from Existing Implementations

### Sequence.xyz Implementation

- **Overall Compression:** ~5x reduction in calldata size
- **Gas Savings:** ~50% reduction in transaction costs on L2s
- **Networks Deployed:** Arbitrum, Arbitrum Nova, Optimism, Base
- **Specific Results:**
  - First-time ETH transfers: 15% gas reduction
  - Subsequent ETH transfers: 47% gas reduction
  - ERC20 transfers: 50-54% gas reduction
  - ERC20 approvals: 52% gas reduction
  - Uniswap swaps: up to 56% gas reduction

### Theoretical Limits (Vitalik's Analysis)

- Current typical rollup transaction: ~180 bytes
- Theoretical minimum with optimal compression: <25 bytes
- Potential throughput improvement: from ~7,407 TPS to >50,000 TPS (with 16MB blocks)

## Network-Specific Considerations

Different networks benefit differently from compression techniques:

### Optimistic Rollups (Arbitrum, Optimism)
- Benefit significantly from all compression techniques
- Calldata is a major cost factor

### ZK Rollups (zkSync, StarkNet)
- Can leverage state diff compression more effectively
- May have different data structures requiring specialized approaches

### L1 Networks (Ethereum, Polygon)
- Less benefit from compression due to different gas cost models
- Calldata is relatively cheaper compared to L2s

## Conclusion

Compression techniques show significant potential for reducing rollup costs and increasing throughput. Production implementations have already demonstrated 50%+ gas savings on major L2 networks, validating the approach. The most effective strategies combine multiple techniques tailored to specific transaction patterns and network characteristics. 