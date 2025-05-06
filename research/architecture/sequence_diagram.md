# ZeroCompress: Sequence Diagram

## Compression Sequence

```
┌────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  ┌──────────────┐
│ DApp/User  │  │Integration   │  │  Transaction  │  │  Strategy    │  │ Compression   │  │ Rollup Adapter │  │ L2 Network  │
│            │  │SDK           │  │  Analyzer     │  │  Selector    │  │ Engine        │  │                │  │             │
└─────┬──────┘  └──────┬───────┘  └───────┬───────┘  └──────┬───────┘  └───────┬───────┘  └────────┬───────┘  └──────┬──────┘
      │                │                  │                  │                  │                   │                 │
      │  1. Create Txn │                  │                  │                  │                   │                 │
      │────────────────>                  │                  │                  │                   │                 │
      │                │                  │                  │                  │                   │                 │
      │                │  2. Analyze Txn  │                  │                  │                   │                 │
      │                │─────────────────>│                  │                  │                   │                 │
      │                │                  │                  │                  │                   │                 │
      │                │                  │  3. Patterns &   │                  │                   │                 │
      │                │                  │  Statistics      │                  │                   │                 │
      │                │                  │─────────────────>│                  │                   │                 │
      │                │                  │                  │                  │                   │                 │
      │                │                  │                  │ 4. Select        │                   │                 │
      │                │                  │                  │ Strategy         │                   │                 │
      │                │                  │                  │────────────────> │                   │                 │
      │                │                  │                  │                  │                   │                 │
      │                │  5. Compression Request             │                  │                   │                 │
      │                │────────────────────────────────────>│                  │                   │                 │
      │                │                  │                  │                  │                   │                 │
      │                │                  │                  │                  │  6. Compress Data │                 │
      │                │                  │                  │                  │ (internal)        │                 │
      │                │                  │                  │                  │                   │                 │
      │                │                  │                  │                  │ 7. Adapt for L2   │                 │
      │                │                  │                  │                  │─────────────────> │                 │
      │                │                  │                  │                  │                   │                 │
      │                │                  │                  │                  │                   │ 8. Format for L2│
      │                │                  │                  │                  │                   │ (internal)      │
      │                │                  │                  │                  │                   │                 │
      │                │  9. Compressed Transaction          │                  │                   │                 │
      │                │<───────────────────────────────────────────────────────────────────────────│                 │
      │                │                  │                  │                  │                   │                 │
      │ 10. Submit Txn │                  │                  │                  │                   │                 │
      │<───────────────│                  │                  │                  │                   │                 │
      │                │                  │                  │                  │                   │                 │
      │ 11. Send to L2 │                  │                  │                  │                   │                 │
      │─────────────────────────────────────────────────────────────────────────────────────────────────────────────>│
      │                │                  │                  │                  │                   │                 │
```

## Decompression Sequence

```
┌────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐
│ L2 Network │  │Decompression │  │ Security      │  │Decompression │  │ Storage       │  │ Target        │
│            │  │Gateway       │  │ Verifier      │  │Modules       │  │ Registry      │  │ Contract      │
└─────┬──────┘  └──────┬───────┘  └───────┬───────┘  └──────┬───────┘  └───────┬───────┘  └────────┬───────┘
      │                │                  │                  │                  │                   │
      │1. Compressed   │                  │                  │                  │                   │
      │  Transaction   │                  │                  │                  │                   │
      │────────────────>                  │                  │                  │                   │
      │                │                  │                  │                  │                   │
      │                │2. Verify         │                  │                  │                   │
      │                │Integrity         │                  │                  │                   │
      │                │─────────────────>│                  │                  │                   │
      │                │                  │                  │                  │                   │
      │                │3. Verification   │                  │                  │                   │
      │                │Result            │                  │                  │                   │
      │                │<─────────────────│                  │                  │                   │
      │                │                  │                  │                  │                   │
      │                │4. Select         │                  │                  │                   │
      │                │Decompress Modules│                  │                  │                   │
      │                │─────────────────────────────────────>                  │                   │
      │                │                  │                  │                  │                   │
      │                │                  │                  │5. Check Address  │                   │
      │                │                  │                  │  Registry        │                   │
      │                │                  │                  │─────────────────>│                   │
      │                │                  │                  │                  │                   │
      │                │                  │                  │6. Address Data   │                   │
      │                │                  │                  │<─────────────────│                   │
      │                │                  │                  │                  │                   │
      │                │                  │                  │7. Register New   │                   │
      │                │                  │                  │  Addresses       │                   │
      │                │                  │                  │─────────────────>│                   │
      │                │                  │                  │                  │                   │
      │                │                  │                  │8. Decompress     │                   │
      │                │                  │                  │(internal process)│                   │
      │                │                  │                  │                  │                   │
      │                │9. Decompressed   │                  │                  │                   │
      │                │Data              │                  │                  │                   │
      │                │<─────────────────────────────────────                  │                   │
      │                │                  │                  │                  │                   │
      │                │10. Forward to    │                  │                  │                   │
      │                │Target            │                  │                  │                   │
      │                │──────────────────────────────────────────────────────────────────────────>│
      │                │                  │                  │                  │                   │
      │                │                  │                  │                  │                   │11. Execute
      │                │                  │                  │                  │                   │Transaction
      │                │                  │                  │                  │                   │(internal)
      │                │                  │                  │                  │                   │
```

## Address Registration Sequence

```
┌────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐
│User/DApp   │  │Compression   │  │ On-chain      │  │ Storage      │
│            │  │Engine        │  │ Decompression │  │ Registry     │
└─────┬──────┘  └──────┬───────┘  └───────┬───────┘  └──────┬───────┘
      │                │                  │                  │
      │ 1. Transaction │                  │                  │
      │ with new addr  │                  │                  │
      │────────────────>                  │                  │
      │                │                  │                  │
      │                │ 2. Compress with │                  │
      │                │ full address     │                  │
      │                │ (internal)       │                  │
      │                │                  │                  │
      │                │ 3. Compressed    │                  │
      │                │ transaction      │                  │
      │                │─────────────────>│                  │
      │                │                  │                  │
      │                │                  │ 4. Recognize new │
      │                │                  │ address          │
      │                │                  │─────────────────>│
      │                │                  │                  │
      │                │                  │                  │ 5. Store address
      │                │                  │                  │ with new index
      │                │                  │                  │ (internal)
      │                │                  │                  │
      │                │                  │ 6. Confirmation  │
      │                │                  │<─────────────────│
      │                │                  │                  │
      │                │                  │ 7. Complete      │
      │                │                  │ decompression    │
      │                │                  │ (internal)       │
      │                │                  │                  │
      │ 8. New         │                  │                  │
      │ transaction    │                  │                  │
      │ with same addr │                  │                  │
      │────────────────>                  │                  │
      │                │                  │                  │
      │                │ 9. Check if addr │                  │
      │                │ is registered    │                  │
      │                │─────────────────────────────────────>
      │                │                  │                  │
      │                │ 10. Return index │                  │
      │                │<─────────────────────────────────────
      │                │                  │                  │
      │                │ 11. Compress with│                  │
      │                │ address index    │                  │
      │                │ (internal)       │                  │
      │                │                  │                  │
      │                │ 12. Compressed   │                  │
      │                │ transaction      │                  │
      │                │ (with index)     │                  │
      │                │─────────────────>│                  │
      │                │                  │                  │
      │                │                  │ 13. Look up addr │
      │                │                  │ from index       │
      │                │                  │─────────────────>│
      │                │                  │                  │
      │                │                  │ 14. Return addr  │
      │                │                  │<─────────────────│
      │                │                  │                  │
      │                │                  │ 15. Complete     │
      │                │                  │ decompression    │
      │                │                  │ (internal)       │
      │                │                  │                  │
```

## Key Points in the Sequence

### Compression Process
1. The process begins when a DApp creates a transaction and passes it to the Integration SDK
2. Transaction Analyzer examines the transaction structure to find compression opportunities
3. Strategy Selector determines the optimal compression approach
4. Compression Engine applies the selected strategy
5. Rollup Adapter formats the compressed transaction for the specific L2 network
6. The compressed transaction is sent to the L2 network

### Decompression Process
1. The L2 network receives the compressed transaction and forwards it to the Decompression Gateway
2. Security verification ensures the compressed data is valid
3. Appropriate Decompression Modules are selected
4. Storage Registry is consulted for address lookups if needed
5. Decompression is performed and the original transaction data is reconstructed
6. Decompressed transaction is forwarded to the target contract
7. Target contract executes the transaction

### Address Registration Process
1. New addresses in transactions are compressed with their full value initially
2. During decompression, these addresses are registered in the Storage Registry
3. Future transactions can reference these addresses by their index
4. This creates a virtuous cycle where frequently used addresses are represented using minimal calldata 