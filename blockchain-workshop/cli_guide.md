# Blockchain CLI Guide

## Overview
The Blockchain CLI provides a command-line interface to interact with the blockchain server. All commands support the `--help` flag to display usage information.

## User Management

### Creating New Users
Users must be explicitly created before they can participate in transactions. Each new user starts with a balance of **$100.00**.

**Usage:**
```bash
python -m cli.cli create-user <username>
```

**Example:**
```bash
# Create users named 'alice' and 'bob'
python -m cli.cli create-user alice
python -m cli.cli create-user bob
```

### Viewing User Balances
Check the current balance of all users:
```bash
python -m cli.cli show-balances
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
python -m cli.cli add-transaction <source> <recipient> <amount>
```

**Example:**
```bash
# Send 10.0 from alice to bob
python -m cli.cli add-transaction alice bob 10.0
```

**Note:** If either the source or recipient user doesn't exist, the transaction will fail and be logged as an invalid transaction.

### View the Blockchain
Display the entire blockchain with all transactions.

**Usage:**
```bash
python -m cli.cli show-chain
```

### View a Block
Display a specific block by its index.

**Usage:**
```bash
python -m cli.cli show-block <index>
```

**Example:**
```bash
python -m cli.cli show-block 1
```

### View Balances
Display the current balance of all accounts.

**Usage:**
```bash
python -m cli.cli show-balances
```

### View Pending Transactions

Show transactions that are pending and not yet in a block.

```bash
python -m cli.cli show-pending
```

### View Invalid Transactions

Show all transactions that failed validation with their error messages.

```bash
python -m cli.cli show-invalid
```

### Export Blockchain Data

Export the entire blockchain data (blocks, transactions, balances) to a JSON file.

**Usage:**
```bash
python -m cli.cli export <filepath>
```

**Example:**
```bash
python -m cli.cli export blockchain_export.json
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
   python -m cli.cli create-user alice
   python -m cli.cli create-user bob
   python -m cli.cli create-user charlie
   
   # Check initial balances
   python -m cli.cli show-balances
   
   # Add some transactions
   python -m cli.cli add-transaction alice bob 10.0
   python -m cli.cli add-transaction bob charlie 5.0
   
   # View the blockchain
   python -m cli.cli show-chain

   # View a specific block (1-indexed)
   python -m cli.cli show-block 2
   
   # Check updated balances
   python -m cli.cli show-balances
   
   # View pending transactions
   python -m cli.cli show-pending

   # Export blockchain data
   python -m cli.cli export blockchain_data.json
   ```

2. **Error handling examples**:
   ```bash
   # Non-existent user transaction (will fail and appear in invalid transactions)
   python -m cli.cli add-transaction alice dave 10.0
   
   # Insufficient funds transaction
   python -m cli.cli add-transaction alice bob 1000.0
   
   # View invalid transactions
   python -m cli.cli show-invalid
   
   # Reset the blockchain
   python -m cli.cli reset
   ```
