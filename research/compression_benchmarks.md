# ZeroCompress: Compression Benchmarks Analysis

## Summary of Compression Potential

This document analyzes the potential compression ratios and gas savings achievable with different compression techniques, based on existing implementations and theoretical research.

## Transaction Types and Baseline Sizes

| Transaction Type | Uncompressed Size (bytes) | Notes |
|------------------|---------------------------|-------|
| Simple ETH Transfer | ~110-130 | Basic transaction with minimal data |
| ERC20 Transfer | ~180-200 | Includes function selector, address, and amount |
| ERC20 Approval | ~180-200 | Similar to transfer but with approval data |
| Contract Deployment | ~300-2000+ | Varies widely based on contract complexity |
| Complex DEX Swap | ~300-500 | Multiple function calls, addresses, and parameters |
| NFT Mint/Transfer | ~200-300 | Includes token ID and metadata references |

## Compression Results from Sequence.xyz Implementation

| Transaction Type | Compression Ratio | Gas Reduction | Notes |
|------------------|-------------------|---------------|-------|
| ETH Transfer (cold) | ~2x | 15% | First-time addresses require storage |
| ETH Transfer (warm) | ~3x | 47% | Subsequent transfers with known addresses |
| ERC20 Transfer (cold) | ~3.5x | 50.60% | First interaction with token contract |
| ERC20 Transfer (warm) | ~4x | 54.24% | Subsequent interactions |
| ERC20 Approval | ~4x | 52% | Especially efficient for max approvals |
| Uniswap Swap | ~4-5x | up to 56% | Complex transaction with multiple parts |

## Theoretical Compression Limits (Vitalik's Analysis)

| Technique | Compression Potential | Current Implementation Status |
|-----------|----------------------|-------------------------------|
| Zero-byte Elimination | 2-3x | Widely implemented, including Sequence.xyz |
| Address Pointer Compression | 4-5x | Implemented by Sequence.xyz with 2-4 byte pointers |
| Value Serialization | 2-4x | Partially implemented for common values |
| BLS Signature Aggregation | 5-10x | Experimental, implemented in BLS Wallet |
| State Diff Compression | 10-20x | Theoretical for ZK rollups, limited implementations |

## Estimated Total Compression Potential

| Compression Level | Techniques Used | Overall Reduction | Bytes per Tx | TPS Potential* |
|-------------------|-----------------|-------------------|--------------|----------------|
| Basic | Zero-byte elimination | 2-3x | 60-90 bytes | 14,000-21,000 |
| Intermediate | + Address compression, Value serialization | 4-5x | 35-45 bytes | 30,000-38,000 |
| Advanced | + Signature aggregation | 5-8x | 22-35 bytes | 38,000-60,000 |
| Theoretical Maximum | All techniques optimized | 7-10x | <25 bytes | >50,000 |

*TPS (Transactions Per Second) potential based on 16MB blocks as referenced in Vitalik's analysis

## Network-Specific Compression Performance

### Optimistic Rollups (Arbitrum, Optimism)

| Technique | Effectiveness | Notes |
|-----------|--------------|-------|
| Zero-byte Elimination | High | Particularly effective due to calldata cost model |
| Address Compression | High | Very effective for repeated contract interactions |
| Value Serialization | Medium-High | Effective for common values |
| Signature Aggregation | Potentially High | Would require protocol changes |
| Combined Approach | Very High | 50-60% gas reduction demonstrated by Sequence |

### ZK Rollups (zkSync, StarkNet)

| Technique | Effectiveness | Notes |
|-----------|--------------|-------|
| Zero-byte Elimination | Medium-High | Effective but different data structures |
| Address Compression | Medium-High | Effective for repeated addresses |
| Value Serialization | Medium | Different encoding may be used already |
| State Diff Compression | Very High | Potentially more efficient than transaction compression |
| Combined Approach | Very High | Potentially 60-80% reduction with optimized approach |

## Gas Cost Analysis

### Compression vs. Decompression Gas Costs

| Compression Technique | Calldata Savings | Decompression Cost | Net Savings | Notes |
|-----------------------|------------------|-------------------|-------------|-------|
| Zero-byte Elimination | 15-30% | Very Low | 15-25% | Simple, efficient decompression |
| Address Compression | 30-50% | Low-Medium | 25-45% | Requires storage lookups |
| Value Serialization | 10-30% | Low | 10-25% | Simple decoding logic |
| Signature Aggregation | 40-60% | High | 20-40% | Computationally intensive verification |
| Combined (Sequence.xyz) | 70-80% | Medium | ~50% | Balance of techniques |

### Cost Model Example (Based on Sequence Data)

For an ERC20 transfer on Arbitrum:

```
Without compression:
- Total gas: ~100,000 gas
- Cost @ 0.1 gwei: ~0.01 ETH

With compression:
- Total gas: ~50,000 gas
- Cost @ 0.1 gwei: ~0.005 ETH
- Savings: ~50%
```

## Conclusion

The benchmarks demonstrate that:

1. A 4-5x compression ratio is achievable with existing techniques (as proven by Sequence.xyz)
2. This translates to approximately 50% gas cost reduction on L2 networks
3. More advanced techniques could potentially reach 7-10x compression
4. Different networks and transaction types benefit differently from various compression techniques

ZeroCompress will aim to match and exceed these benchmarks by combining the most effective techniques in a modular framework, with specific optimizations for different rollup implementations. 