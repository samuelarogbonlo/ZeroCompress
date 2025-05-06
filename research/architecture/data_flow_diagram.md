# ZeroCompress: Data Flow Diagram

## Transaction Compression Flow

```
┌─────────────┐         ┌─────────────────┐         ┌──────────────────┐
│             │         │                 │         │                  │
│ Application │ ──────► │ Integration SDK │ ──────► │ Transaction      │
│             │   Raw   │                 │   Raw   │ Analyzer         │
└─────────────┘   Txn   └─────────────────┘   Txn   └──────────────────┘
                                                          │
                                                          │ Transaction
                                                          │ Patterns
                                                          ▼
┌─────────────────┐         ┌─────────────────┐    ┌──────────────────┐
│                 │         │                 │    │                  │
│ Rollup-Specific │ ◄────── │ Compression     │ ◄──┤ Strategy         │
│ Adapter         │ Optimized │ Engine        │    │ Selector         │
└─────────────────┘ Format  └─────────────────┘    └──────────────────┘
        │                          ▲
        │ Network-                 │ Compression
        │ Specific                 │ Configuration
        │ Format                   │
        ▼                   ┌─────────────────┐
┌─────────────────┐         │                 │
│                 │         │ Benchmarking    │
│ L2 Network      │         │ Tools           │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
```

## Transaction Decompression Flow

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│ L2 Network      │ ──────► │ Decompression   │ ──────► │ Security        │
│                 │ Compressed │ Gateway      │ Parsed  │ Verifier        │
└─────────────────┘   Data  └─────────────────┘  Data   └─────────────────┘
                                 │                             │
                                 │ Compression                 │ Verified
                                 │ Format ID                   │ Data
                                 ▼                             │
                        ┌─────────────────┐                    │
                        │                 │                    │
                        │ Decompression   │ ◄─────────────────┘
                        │ Modules         │
                        └─────────────────┘
                                 │
                                 │ Module
                                 │ Selection
                                 ▼
     ┌────────────┬──────────────┬──────────────┬──────────────┐
     │            │              │              │              │
     ▼            ▼              ▼              ▼              ▼
┌──────────┐ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐
│          │ │          │  │          │  │          │  │             │
│ Zero     │ │ Address  │  │ Value    │  │ Signature│  │ Other       │
│ Compressor│ │Compressor│  │Compressor│  │Aggregator│  │ Modules    │
└──────────┘ └──────────┘  └──────────┘  └──────────┘  └─────────────┘
     │            │              │              │              │
     └────────────┴──────────────┴──────────────┴──────────────┘
                                 │
                                 │ Decompressed
                                 │ Data
                                 ▼
                        ┌─────────────────┐        ┌─────────────────┐
                        │                 │        │                 │
                        │ Router Module   │───────►│ Target Contract │
                        │                 │        │                 │
                        └─────────────────┘        └─────────────────┘
```

## Storage Registry Interaction Flow

```
                        ┌─────────────────┐
                        │                 │
           ┌───────────►│ Storage Registry│◄────────────┐
           │            │                 │             │
           │            └─────────────────┘             │
           │                    ▲                       │
           │                    │                       │
      Read │                    │ Write                 │ Read
    Address│                    │ Address               │ Address
           │                    │                       │
           │                    │                       │
           ▼                    │                       ▼
┌─────────────────┐      ┌─────────────────┐    ┌─────────────────┐
│                 │      │                 │    │                 │
│ Address         │      │ Decompression   │    │ Other           │
│ Compressor      │      │ Gateway         │    │ Modules         │
│                 │      │                 │    │                 │
└─────────────────┘      └─────────────────┘    └─────────────────┘
```

## Data Transformations

### Raw Transaction → Compressed Transaction

```
┌────────────────────────────────────────────────────────────┐
│ Raw Transaction Data (Example ERC20 Transfer)              │
├────────────────────────────────────────────────────────────┤
│ Function Selector: 0xa9059cbb (transfer)                   │
│ Parameter 1: 0x0000...000071C7656EC7ab88b098defB751B7401B5f│ To Address
│ Parameter 2: 0x0000...0000000000000000000000000004e1003b28 │ Amount
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Compression Process                                        │
├────────────────────────────────────────────────────────────┤
│ 1. Identify function selector (transfer = 0xa9059cbb)      │
│ 2. Identify zero-bytes for compression                     │
│ 3. Check if addresses exist in registry                    │
│ 4. Optimize value representation                           │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Compressed Transaction Data                                │
├────────────────────────────────────────────────────────────┤
│ Format ID: 0x37 (Indicates compression algorithm used)     │
│ Selector Index: 0x03 (Index of transfer function)          │
│ Address Encoding: 0x0001 (Index to address if in registry) │
│ Value Encoding: 0x4e1003b28 (Compact value representation) │
└────────────────────────────────────────────────────────────┘
```

### Compressed Transaction → Decompressed Transaction

```
┌────────────────────────────────────────────────────────────┐
│ Compressed Transaction Data                                │
├────────────────────────────────────────────────────────────┤
│ Format ID: 0x37 (Indicates compression algorithm used)     │
│ Selector Index: 0x03 (Index of transfer function)          │
│ Address Encoding: 0x0001 (Index to address if in registry) │
│ Value Encoding: 0x4e1003b28 (Compact value representation) │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Decompression Process                                      │
├────────────────────────────────────────────────────────────┤
│ 1. Parse format ID to select decompression algorithm       │
│ 2. Look up function selector from index                    │
│ 3. Retrieve address from storage registry                  │
│ 4. Expand compact value representation                     │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ Decompressed Transaction Data                              │
├────────────────────────────────────────────────────────────┤
│ Function Selector: 0xa9059cbb (transfer)                   │
│ Parameter 1: 0x0000...000071C7656EC7ab88b098defB751B7401B5f│
│ Parameter 2: 0x0000...0000000000000000000000000004e1003b28 │
└────────────────────────────────────────────────────────────┘
```

## Data Flow for Major Use Cases

### 1. DApp Integration

1. DApp prepares transaction for submission to L2
2. Integration SDK intercepts the transaction
3. Transaction Analyzer examines the transaction structure
4. Strategy Selector chooses optimal compression technique
5. Compression Engine compresses the transaction
6. Rollup Adapter formats the compressed transaction for the target L2
7. Compressed transaction is submitted to the L2 network

### 2. On-chain Decompression

1. Compressed transaction arrives at Decompression Gateway
2. Gateway identifies compression format and parses the data
3. Security Verifier checks data integrity
4. Decompression Modules are selected based on format
5. Modules work in sequence to decompress the data
6. Router Module forwards decompressed data to target contract
7. Target contract executes the decompressed transaction

### 3. Address Registry Management

1. New addresses are identified during compression
2. Addresses are stored in Storage Registry during decompression
3. Future transactions can reference addresses by index
4. Address Compressor retrieves addresses from Storage Registry
5. Storage Registry maintains the mapping between indices and addresses