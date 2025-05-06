# ZeroCompress: Component Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            ZeroCompress System                              │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                 ┌──────────────────┬┴┬──────────────────┐
                 │                  │  │                  │
                 ▼                  ▼  │                  ▼
┌────────────────────────┐ ┌────────────────┐ ┌────────────────────────┐
│ Off-chain Components    │ │  Contracts     │ │ Integration Components │
└────────────────────────┘ └────────────────┘ └────────────────────────┘
            │                      │                    │
  ┌─────────┼─────────┐            │         ┌─────────┼─────────┐
  │         │         │            │         │         │         │
  ▼         ▼         ▼            │         ▼         ▼         ▼
┌─────┐  ┌─────┐  ┌─────┐          │    ┌─────────┐ ┌─────┐ ┌──────────┐
│  1  │  │  2  │  │  3  │          │    │    11   │ │ 12  │ │    13    │
└─────┘  └─────┘  └─────┘          │    └─────────┘ └─────┘ └──────────┘
                                    │
                     ┌──────────────┼───────────────────┐
                     │              │                   │
                     ▼              ▼                   ▼
                 ┌─────────┐  ┌─────────────┐  ┌──────────────┐
                 │    4    │  │      5      │  │      6       │
                 └─────────┘  └─────────────┘  └──────────────┘
                     │              │                  │
         ┌───────────┼──────┐       │          ┌──────┼───────┐
         │           │      │       │          │      │       │
         ▼           ▼      ▼       ▼          ▼      ▼       ▼
     ┌─────────┐ ┌─────┐ ┌─────┐ ┌─────┐  ┌─────┐ ┌─────┐ ┌─────┐
     │    7    │ │  8  │ │  9  │ │ 10  │  │ 14  │ │ 15  │ │ 16  │
     └─────────┘ └─────┘ └─────┘ └─────┘  └─────┘ └─────┘ └─────┘
```

## Component Legend

### Off-chain Components
1. **Compression Engine**: Core algorithms for data compression
   - Depends on: Transaction Analyzer, Compression Strategy Selector
   - Used by: DApp Integration SDK, CLI Tools

2. **Transaction Analyzer**: Analyzes transaction patterns to optimize compression
   - Depends on: None
   - Used by: Compression Engine, Benchmarking Tools

3. **Compression Strategy Selector**: Dynamically selects optimal compression techniques
   - Depends on: Transaction Analyzer
   - Used by: Compression Engine

### On-chain Contracts
4. **Decompression Gateway**: Entry point for compressed transactions
   - Depends on: Decompression Modules
   - Used by: All client applications

5. **Decompression Modules**: Specialized decompression algorithms
   - Depends on: None
   - Used by: Decompression Gateway

6. **Storage Registry**: Manages address and data mappings for compression
   - Depends on: None
   - Used by: Decompression Gateway, Decompression Modules

7. **Zero Compressor Module**: Handles zero-byte elimination
   - Depends on: None
   - Used by: Decompression Modules

8. **Address Compressor Module**: Handles address compression
   - Depends on: Storage Registry
   - Used by: Decompression Modules

9. **Value Compressor Module**: Handles transaction value compression
   - Depends on: None
   - Used by: Decompression Modules

10. **Signature Aggregator Module**: Handles BLS signature aggregation
    - Depends on: None
    - Used by: Decompression Modules

### Integration Components
11. **Rollup Adapters**: Network-specific adapters for different L2s
    - Depends on: Compression Engine
    - Used by: DApp Integration SDK

12. **DApp Integration SDK**: SDK for DApp developers to integrate compression
    - Depends on: Compression Engine, Rollup Adapters
    - Used by: External applications

13. **Benchmarking Tools**: Measures compression performance and savings
    - Depends on: Transaction Analyzer
    - Used by: Development team, external evaluators

### Supporting Modules
14. **Security Verifier**: Ensures integrity of compressed data
    - Depends on: None
    - Used by: Decompression Gateway

15. **Router Module**: Routes decompressed data to destination contracts
    - Depends on: None
    - Used by: Decompression Gateway

16. **Fallback Handler**: Handles decompression failures gracefully
    - Depends on: None
    - Used by: Decompression Gateway

## Component Relationships

### Key Dependencies

- The **Compression Engine** (1) relies on the **Transaction Analyzer** (2) to identify patterns that can be optimized.
- All decompression modules (7-10) are orchestrated by the **Decompression Modules** component (5).
- The **Address Compressor Module** (8) requires the **Storage Registry** (6) to store and retrieve address mappings.
- **Rollup Adapters** (11) customize the compression for specific L2 networks.

### Data Flow

- Transaction data flows from external applications through the **DApp Integration SDK** (12) to the **Compression Engine** (1).
- Compressed data is sent to the **Decompression Gateway** (4) on-chain.
- The gateway routes the compressed data to appropriate **Decompression Modules** (5).
- After decompression, the **Router Module** (15) forwards the data to its final destination.

### Extensibility Points

- New compression techniques can be added by extending the **Compression Engine** (1) and adding corresponding modules in **Decompression Modules** (5).
- Support for new L2 networks is added through the **Rollup Adapters** (11).
- Additional security measures can be implemented in the **Security Verifier** (14). 