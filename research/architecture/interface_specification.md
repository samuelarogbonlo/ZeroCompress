# ZeroCompress: Interface Specification

This document defines the key interfaces and API specifications for the ZeroCompress system components.

## 1. Off-chain Components

### 1.1. Compression Engine API

#### 1.1.1 Transaction Compression

```typescript
/**
 * Compresses a raw transaction for submission to an L2 network
 * 
 * @param transaction - The raw transaction to compress
 * @param options - Configuration options for compression
 * @returns A compressed transaction ready for submission
 */
function compressTransaction(
  transaction: RawTransaction,
  options?: CompressionOptions
): CompressedTransaction;

/**
 * Options for transaction compression
 */
interface CompressionOptions {
  /**
   * Target L2 network for compression optimization
   */
  network: NetworkType;
  
  /**
   * Compression techniques to apply (defaults to all)
   */
  techniques?: CompressionTechnique[];
  
  /**
   * Optimization level (higher = more compression, potentially more computation)
   */
  optimizationLevel?: OptimizationLevel;
  
  /**
   * Whether to use the address registry for compression
   */
  useAddressRegistry?: boolean;
  
  /**
   * Address of the decompression contract on the target network
   */
  decompressionContract?: string;
}

/**
 * Supported compression techniques
 */
enum CompressionTechnique {
  ZERO_BYTE_ELIMINATION = 'zero-byte',
  ADDRESS_COMPRESSION = 'address',
  VALUE_SERIALIZATION = 'value',
  SIGNATURE_AGGREGATION = 'signature',
}

/**
 * Supported L2 networks
 */
enum NetworkType {
  ARBITRUM = 'arbitrum',
  OPTIMISM = 'optimism',
  BASE = 'base',
  ZK_SYNC = 'zksync',
  STARKNET = 'starknet',
}

/**
 * Optimization level for compression
 */
enum OptimizationLevel {
  MINIMAL = 1,  // Basic compression, fastest
  BALANCED = 2, // Default balance of compression/speed
  MAXIMUM = 3   // Maximum compression, potentially slower
}
```

#### 1.1.2 Compression Statistics

```typescript
/**
 * Estimates gas savings from compression
 * 
 * @param transaction - Raw transaction to analyze
 * @param options - Compression options
 * @returns Detailed compression statistics
 */
function estimateCompression(
  transaction: RawTransaction, 
  options?: CompressionOptions
): CompressionStats;

/**
 * Statistics about compression results
 */
interface CompressionStats {
  /**
   * Original size in bytes
   */
  originalSize: number;
  
  /**
   * Compressed size in bytes
   */
  compressedSize: number;
  
  /**
   * Compression ratio (originalSize / compressedSize)
   */
  compressionRatio: number;
  
  /**
   * Estimated gas savings in the target network
   */
  estimatedGasSavings: number;
  
  /**
   * Breakdown of savings by compression technique
   */
  savingsByTechnique: Record<CompressionTechnique, number>;
  
  /**
   * Estimated gas cost for decompression
   */
  decompressionCost: number;
  
  /**
   * Net gas savings (estimatedGasSavings - decompressionCost)
   */
  netGasSavings: number;
}
```

### 1.2. Transaction Analyzer API

```typescript
/**
 * Analyzes a transaction to identify compression opportunities
 * 
 * @param transaction - The transaction to analyze
 * @returns Analysis results with compression recommendations
 */
function analyzeTransaction(
  transaction: RawTransaction
): TransactionAnalysis;

/**
 * Results of transaction analysis
 */
interface TransactionAnalysis {
  /**
   * Transaction type identification
   */
  transactionType: TransactionType;
  
  /**
   * Percentage of zero bytes in the transaction
   */
  zeroBytePercentage: number;
  
  /**
   * Addresses found in the transaction
   */
  addresses: string[];
  
  /**
   * Values found in the transaction that can be compressed
   */
  compressibleValues: CompressibleValue[];
  
  /**
   * Recommended compression techniques for this transaction
   */
  recommendedTechniques: CompressionTechnique[];
  
  /**
   * Predicted compression ratio if all recommended techniques are applied
   */
  predictedCompressionRatio: number;
}

/**
 * Categories of transaction types
 */
enum TransactionType {
  ETH_TRANSFER = 'eth-transfer',
  ERC20_TRANSFER = 'erc20-transfer',
  ERC20_APPROVAL = 'erc20-approval',
  ERC721_TRANSFER = 'erc721-transfer',
  DEX_SWAP = 'dex-swap',
  CONTRACT_DEPLOYMENT = 'contract-deployment',
  CONTRACT_INTERACTION = 'contract-interaction',
  MULTI_CALL = 'multi-call',
  OTHER = 'other'
}

/**
 * Representation of a value that can be compressed
 */
interface CompressibleValue {
  /**
   * Original value
   */
  value: string;
  
  /**
   * Position in the transaction data
   */
  position: number;
  
  /**
   * Recommended compression technique
   */
  recommendedTechnique: CompressionTechnique;
  
  /**
   * Estimated size after compression
   */
  compressedSize: number;
}
```

### 1.3. DApp Integration SDK

```typescript
/**
 * Client for compressing transactions
 */
class ZeroCompressClient {
  /**
   * Creates a new ZeroCompress client
   * 
   * @param config - Configuration for the client
   */
  constructor(config: ZeroCompressConfig);
  
  /**
   * Compresses a transaction for submission to an L2
   * 
   * @param transaction - Raw transaction to compress
   * @returns Compressed transaction
   */
  compressTransaction(transaction: RawTransaction): Promise<CompressedTransaction>;
  
  /**
   * Submits a compressed transaction to the L2
   * 
   * @param compressedTransaction - Transaction to submit
   * @returns Transaction hash
   */
  submitCompressedTransaction(compressedTransaction: CompressedTransaction): Promise<string>;
  
  /**
   * Estimates gas savings from compression
   * 
   * @param transaction - Transaction to analyze
   * @returns Compression statistics
   */
  estimateGasSavings(transaction: RawTransaction): Promise<CompressionStats>;
}

/**
 * Configuration for ZeroCompress client
 */
interface ZeroCompressConfig {
  /**
   * Target network for compression
   */
  network: NetworkType;
  
  /**
   * Provider URL for the target network
   */
  providerUrl: string;
  
  /**
   * Address of the decompression contract
   */
  decompressionContract: string;
  
  /**
   * Compression options
   */
  compressionOptions?: CompressionOptions;
}
```

## 2. On-chain Components

### 2.1. Decompression Gateway Interface

```solidity
/**
 * Interface for the main decompression gateway contract
 */
interface IDecompressionGateway {
    /**
     * Decompresses data and forwards to target contract
     * @param compressedData The compressed transaction data
     * @param target The target contract address
     * @return The result of the call to the target contract
     */
    function decompressAndForward(
        bytes calldata compressedData,
        address target
    ) external payable returns (bytes memory);
    
    /**
     * Decompresses data and returns it without forwarding
     * @param compressedData The compressed data
     * @return The decompressed data
     */
    function decompressOnly(
        bytes calldata compressedData
    ) external view returns (bytes memory);
    
    /**
     * Returns the address of a decompression module
     * @param moduleId The ID of the module
     * @return The address of the module
     */
    function getDecompressionModule(
        uint8 moduleId
    ) external view returns (address);
}
```

### 2.2. Storage Registry Interface

```solidity
/**
 * Interface for the storage registry contract
 */
interface IStorageRegistry {
    /**
     * Registers an address and returns its index
     * @param addr The address to register
     * @return index The index assigned to the address
     */
    function registerAddress(
        address addr
    ) external returns (uint32 index);
    
    /**
     * Gets an address by its index
     * @param index The index of the address
     * @return The address at the specified index
     */
    function getAddressByIndex(
        uint32 index
    ) external view returns (address);
    
    /**
     * Gets the index of an address
     * @param addr The address to look up
     * @return The index of the address, or 0 if not registered
     */
    function getAddressIndex(
        address addr
    ) external view returns (uint32);
    
    /**
     * Registers a bytes32 value and returns its index
     * @param value The bytes32 value to register
     * @return index The index assigned to the value
     */
    function registerBytes32(
        bytes32 value
    ) external returns (uint32 index);
    
    /**
     * Gets a bytes32 value by its index
     * @param index The index of the bytes32 value
     * @return The bytes32 value at the specified index
     */
    function getBytes32ByIndex(
        uint32 index
    ) external view returns (bytes32);
}
```

### 2.3. Decompression Module Interface

```solidity
/**
 * Interface for decompression modules
 */
interface IDecompressionModule {
    /**
     * Decompresses data using this module
     * @param compressedData The compressed data
     * @param registry The storage registry address
     * @return The decompressed data
     */
    function decompress(
        bytes calldata compressedData,
        address registry
    ) external view returns (bytes memory);
    
    /**
     * Returns the module type identifier
     * @return The module type ID
     */
    function moduleType() external pure returns (uint8);
    
    /**
     * Returns the module version
     * @return The version of this module
     */
    function version() external pure returns (uint8);
}
```

## 3. Rollup Adapter Interfaces

### 3.1. Generic Rollup Adapter

```typescript
/**
 * Interface for rollup-specific adapters
 */
interface IRollupAdapter {
  /**
   * Adapts a compressed transaction for a specific L2
   * 
   * @param compressedTransaction - The compressed transaction
   * @returns L2-specific formatted transaction
   */
  adaptTransaction(compressedTransaction: CompressedTransaction): L2Transaction;
  
  /**
   * Gets the target L2 network type
   * 
   * @returns The network type
   */
  getNetworkType(): NetworkType;
  
  /**
   * Gets the address of the decompression contract on this L2
   * 
   * @returns The contract address
   */
  getDecompressionContract(): string;
  
  /**
   * Estimates gas costs for decompression on this L2
   * 
   * @param compressedTransaction - The transaction to estimate
   * @returns Estimated gas cost
   */
  estimateDecompressionGas(compressedTransaction: CompressedTransaction): number;
}
```

### 3.2. Network-Specific Adapter Examples

```typescript
/**
 * Arbitrum-specific adapter implementation
 */
class ArbitrumAdapter implements IRollupAdapter {
  // Implementation details for Arbitrum
}

/**
 * Optimism-specific adapter implementation
 */
class OptimismAdapter implements IRollupAdapter {
  // Implementation details for Optimism
}

/**
 * ZkSync-specific adapter implementation
 */
class ZkSyncAdapter implements IRollupAdapter {
  // Implementation details for ZkSync
}
```

## 4. Data Structures

### 4.1. Transaction Representations

```typescript
/**
 * Raw transaction data
 */
interface RawTransaction {
  /**
   * Transaction type
   */
  type?: number;
  
  /**
   * Target address
   */
  to: string | null;
  
  /**
   * Value in wei
   */
  value: string;
  
  /**
   * Gas limit
   */
  gasLimit: string;
  
  /**
   * Gas price or max fee per gas
   */
  gasPrice?: string;
  
  /**
   * Maximum priority fee per gas (EIP-1559)
   */
  maxPriorityFeePerGas?: string;
  
  /**
   * Maximum fee per gas (EIP-1559)
   */
  maxFeePerGas?: string;
  
  /**
   * Transaction data
   */
  data: string;
  
  /**
   * Chain ID
   */
  chainId: number;
  
  /**
   * Nonce
   */
  nonce: number;
  
  /**
   * Access list (EIP-2930)
   */
  accessList?: AccessListItem[];
}

/**
 * Compressed transaction
 */
interface CompressedTransaction {
  /**
   * Compression format identifier
   */
  formatId: number;
  
  /**
   * Compressed data
   */
  data: string;
  
  /**
   * Target decompression contract
   */
  decompressionContract: string;
  
  /**
   * Original transaction hash for reference
   */
  originalTransactionHash?: string;
  
  /**
   * Network-specific metadata
   */
  metadata?: Record<string, any>;
}

/**
 * Network-specific transaction format
 */
interface L2Transaction {
  /**
   * Target address (decompression contract)
   */
  to: string;
  
  /**
   * Transaction data
   */
  data: string;
  
  /**
   * Value in wei
   */
  value: string;
  
  /**
   * Network-specific fields
   */
  [key: string]: any;
}
```

## 5. Error Handling

```typescript
/**
 * Error codes for the ZeroCompress system
 */
enum ErrorCode {
  // General errors
  INVALID_INPUT = 'invalid-input',
  UNSUPPORTED_NETWORK = 'unsupported-network',
  CONTRACT_NOT_DEPLOYED = 'contract-not-deployed',
  
  // Compression errors
  COMPRESSION_FAILED = 'compression-failed',
  EXCEEDS_SIZE_LIMIT = 'exceeds-size-limit',
  UNSUPPORTED_TRANSACTION_TYPE = 'unsupported-transaction-type',
  
  // Decompression errors
  DECOMPRESSION_FAILED = 'decompression-failed',
  INVALID_COMPRESSION_FORMAT = 'invalid-compression-format',
  SECURITY_VERIFICATION_FAILED = 'security-verification-failed',
  
  // Registry errors
  REGISTRY_FULL = 'registry-full',
  INDEX_NOT_FOUND = 'index-not-found',
  
  // Network errors
  NETWORK_ERROR = 'network-error',
  TRANSACTION_REJECTED = 'transaction-rejected'
}

/**
 * Error thrown by ZeroCompress operations
 */
class ZeroCompressError extends Error {
  /**
   * Error code
   */
  code: ErrorCode;
  
  /**
   * Additional error details
   */
  details?: any;
  
  constructor(code: ErrorCode, message: string, details?: any);
}
```

## 6. Event Definitions

### 6.1. On-chain Events

```solidity
/**
 * Events emitted by the decompression gateway
 */
interface IDecompressionEvents {
    /**
     * Emitted when a transaction is decompressed
     * @param sender The sender of the transaction
     * @param target The target contract
     * @param formatId The compression format ID
     * @param compressedSize The size of the compressed data
     * @param decompressedSize The size of the decompressed data
     */
    event TransactionDecompressed(
        address indexed sender,
        address indexed target,
        uint8 formatId,
        uint32 compressedSize,
        uint32 decompressedSize
    );
    
    /**
     * Emitted when a new address is registered
     * @param addr The registered address
     * @param index The assigned index
     */
    event AddressRegistered(
        address indexed addr,
        uint32 indexed index
    );
    
    /**
     * Emitted when decompression fails
     * @param sender The sender of the transaction
     * @param errorCode The error code
     */
    event DecompressionFailed(
        address indexed sender,
        uint8 errorCode
    );
}
```

### 6.2. Off-chain Events

```typescript
/**
 * Event types for the ZeroCompress client
 */
enum ZeroCompressEventType {
  COMPRESSION_START = 'compression-start',
  COMPRESSION_COMPLETE = 'compression-complete',
  SUBMISSION_START = 'submission-start',
  SUBMISSION_COMPLETE = 'submission-complete',
  ERROR = 'error'
}

/**
 * Event emitted by the ZeroCompress client
 */
interface ZeroCompressEvent {
  /**
   * Event type
   */
  type: ZeroCompressEventType;
  
  /**
   * Event timestamp
   */
  timestamp: number;
  
  /**
   * Event data
   */
  data: any;
}

/**
 * Event listener for ZeroCompress events
 */
type ZeroCompressEventListener = (event: ZeroCompressEvent) => void;
``` 