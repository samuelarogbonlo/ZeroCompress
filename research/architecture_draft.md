# ZeroCompress: Architecture Draft

## System Overview

ZeroCompress will be a modular, open-source framework for compressing rollup transaction data on Ethereum and Ethereum L2 networks. The architecture is designed to maximize compression efficiency while maintaining flexibility across different rollup implementations.

## Core Components

### 1. Compression Library (Off-chain)

**Purpose**: Compress transaction data before submission to rollup networks

**Components**:
- Compression Engine: Core algorithms for data compression
- Transaction Analyzer: Identifies patterns in transaction data
- Compression Strategy Selector: Chooses optimal compression technique based on transaction type
- Address Registry: Manages address mapping for pointer-based compression

**Languages/Technologies**:
- TypeScript/JavaScript (for web integration)
- Rust (for performance-critical components)

### 2. Decompression Contracts (On-chain)

**Purpose**: Decompress transaction data on-chain before execution

**Components**:
- Decompression Gateway: Entry point for compressed transactions
- Decompression Modules: Specialized modules for different compression techniques
- Transaction Router: Routes decompressed data to destination contracts

**Design Patterns**:
- Proxy Pattern: For compatibility with existing contracts
- Factory Pattern: For deploying and managing compression-enabled contracts
- Registry Pattern: For address mapping and state management

### 3. Benchmarking Framework

**Purpose**: Measure compression performance and validate correctness

**Components**:
- Dataset Manager: Manages test transaction datasets
- Compression Analyzer: Measures compression ratios and gas savings
- Test Case Generator: Creates synthetic transactions for testing
- Validation Engine: Ensures decompression produces correct results

### 4. Integration Adapters

**Purpose**: Connect ZeroCompress to different rollup implementations

**Components**:
- Arbitrum Adapter: Optimized for Arbitrum's data structure
- Optimism Adapter: Optimized for Optimism's data structure
- zkSync/StarkNet Adapters: Optimized for ZK rollup data structures

## Compression Techniques

The framework will implement multiple compression techniques with a modular architecture:

### Technique 1: Zero-byte Elimination

**Module**: `ZeroCompressor`
- Implementation: Replace sequences of zero bytes with compact representation
- Configuration: Customizable minimum sequence length and encoding format

### Technique 2: Address Compression

**Module**: `AddressCompressor`
- Implementation: Replace addresses with pointers to previously seen addresses
- Storage Strategy: On-chain mapping with configurable caching strategies

### Technique 3: Value Serialization

**Module**: `ValueCompressor`
- Implementation: Custom encodings for common values (ETH amounts, gas prices)
- Features: Configurable encoding tables for different value patterns

### Technique 4: Signature Aggregation

**Module**: `SignatureAggregator`
- Implementation: BLS signature aggregation with verification
- Compatibility: Integration with ERC-4337 for account abstraction

### Technique 5: State Diff Compression

**Module**: `StateDiffCompressor`
- Implementation: Optimize state difference encoding for ZK rollups
- Features: Configurable compression levels based on rollup requirements

## System Interfaces

### 1. Developer API

```typescript
// Example TypeScript interface
interface CompressorOptions {
  techniques: CompressionTechnique[];
  networkType: NetworkType;
  optimizationLevel: OptimizationLevel;
}

interface TransactionCompressor {
  compress(transaction: Transaction, options?: CompressorOptions): CompressedTransaction;
  estimateGasSavings(transaction: Transaction): GasSavingsEstimate;
}
```

### 2. Contract Interfaces

```solidity
// Example Solidity interface
interface IDecompressor {
    function decompressAndForward(
        bytes calldata compressedData,
        address target
    ) external payable returns (bytes memory);
    
    function registerAddress(address addr) external returns (uint32);
    function getAddressFromIndex(uint32 index) external view returns (address);
}
```

## Implementation Considerations

### Gas Optimization

- Balance compression ratio vs. decompression gas cost
- Use assembly for gas-critical operations
- Optimize storage patterns for different usage scenarios

### Security Measures

- Implement secure address registry with access controls
- Validate all compressed data before execution
- Ensure deterministic decompression results

### Compatibility

- Maintain backward compatibility with existing contracts
- Support multiple rollup implementations with adapters
- Minimize dependencies on specific rollup features

## Deployment Strategy

### Phase 1: Basic Framework

- Implement zero-byte elimination and address compression
- Deploy test contracts on testnets
- Create basic benchmarking tools

### Phase 2: Advanced Features

- Add signature aggregation and value serialization
- Improve benchmarking with real transaction data
- Optimize for specific rollup implementations

### Phase 3: Production Readiness

- Complete security audits
- Implement rollup-specific optimizations
- Create developer documentation and integration guides

## Open Questions

1. How will the system handle address collisions in the registry?
2. What is the optimal storage strategy for historical address mapping?
3. How can we make signature aggregation more compatible with hardware wallets?
4. What are the trade-offs between compression ratio and computational complexity?
5. How can we ensure the framework adapts to evolving rollup implementations? 