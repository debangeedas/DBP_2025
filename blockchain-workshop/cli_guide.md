# Blockchain CLI Guide

## Overview
The Blockchain CLI provides a command-line interface to interact with the blockchain server. All commands support the `--help` flag to display usage information.

**Tip:**
- In **Windows PowerShell**, use `./bcli` or `.\bcli` (dot-slash or dot-backslash) to run the CLI batch file, e.g., `.\bcli sc`. This is because PowerShell does not search the current directory for scripts by default.
- In **Windows Command Prompt**, you can use `bcli` directly, e.g., `bcli sc`.
- On **Mac/Linux**, use the full Python command or set up an alias as described in the setup instructions.


**Command Reference:**

| Short | Long            | Description                                      |
|:-----:|:---------------|:-------------------------------------------------|
| cu    | create-user     | Create a new user with starting balance          |
| at    | add-transaction | Add a new transaction                            |
| sc    | show-chain      | Show the entire blockchain                       |
| sb    | show-block      | Show a specific block                            |
| bal   | show-balances   | Show all account balances                        |
| si    | show-invalid    | Show all invalid transactions with errors        |
| sp    | show-pending    | Show all valid transactions waiting for a block  |
| r     | reset           | Reset the blockchain                             |
| ex    | export          | Export blockchain data to a JSON file            |

**Tip:**
- Use the **short form** (e.g., `bcli cu alice`) for speed and convenience, especially during interactive use or quick testing.
- Use the **long form** (e.g., `bcli create-user alice`) for clarity in scripts, documentation.

All examples below show both formats for your reference.


## User Management

### Creating New Users
Users must be explicitly created before they can participate in transactions. Each new user starts with a balance of **$100.00**.

**Usage:**
```bash
bcli cu <username>
```

**Example:**
```bash
# Create users named 'alice' and 'bob'
bcli cu alice
bcli cu bob
```

### Viewing User Balances
Check the current balance of all users:
```bash
bcli bal
```

Output example:
```
========================================
💰 USER BALANCES
========================================
🟢 alice    $100.00
🟢 bob      $100.00
========================================
```

## Transaction Commands {#transaction-commands}

### Add a Transaction
Add a new transaction to the blockchain. Both the sender and recipient must exist.

**Usage:**
```bash
bcli at <source> <recipient> <amount>
```

**Example:**
```bash
# Send 10.0 from alice to bob
bcli at alice bob 10.0
```

**Note:** If either the source or recipient user doesn't exist, the transaction will fail and be logged as an invalid transaction.

### View the Blockchain
Display the entire blockchain with all transactions.

**Usage:**
```bash
bcli show-chain
```

### View a Block
Display a specific block by its index.

**Usage:**
```bash
bcli sb <index>
```

**Example:**
```bash
bcli sb 1
```

### View Balances
Display the current balance of all accounts.

**Usage:**
```bash
bcli bal
```

### View Pending Transactions

Show transactions that are pending and not yet in a block.

```bash
bcli sp
```

### View Invalid Transactions

Show all transactions that failed validation with their error messages.

```bash
bcli si
```

### Export Blockchain Data

Export the entire blockchain data (blocks, transactions, balances) to a JSON file.

**Usage:**
```bash
bcli ex <filepath>
```

**Example:**
```bash
bcli ex blockchain_export.json
```

The export includes:
- Complete blockchain with all blocks and transactions
- Current user balances
- Pending transactions
- Invalid transactions
- Blockchain statistics

## Examples

1. **Complete transaction flow**:
   ```bash
   # Create users first
   bcli cu alice
   bcli cu bob
   bcli cu charlie
   
   # Check initial balances
   bcli bal
   
   # Add some transactions
   bcli at alice bob 10.0
   bcli at bob charlie 5.0
   
   # View the blockchain
   bcli show-chain

   # View a specific block (1-indexed)
   bcli sb 2
   
   # Check updated balances
   bcli bal
   
   # View pending transactions
   bcli sp

   # Export blockchain data
   bcli ex blockchain_data.json
   ```

2. **Error handling examples**:
   ```bash
   # Non-existent user transaction (will fail and appear in invalid transactions)
   bcli at alice dave 10.0
   
   # Insufficient funds transaction
   bcli at alice bob 1000.0
   
   # View invalid transactions
   bcli si
   
   # Reset the blockchain
   bcli r
   ```
