# Blockchain CLI Guide

## Overview
The Blockchain CLI provides a command-line interface to interact with the blockchain server. All commands support the `--help` flag to display usage information.

## User Management

### Creating New Users
New users are automatically created when they first appear in a transaction:
- **As a sender**: New users start with a balance of **$100.00**
- **As a recipient**: New users start with a balance of **$0.00**

**Example:**
```bash
# This will create 'Alice' with $100 and 'Bob' with $0 if they don't exist
python -m cli.cli add-transaction Alice Bob 10.0
```

### Viewing User Balances
Check the current balance of all users:
```bash
python -m cli.cli show-balances
```

## Transaction Commands {#transaction-commands}

### Add a Transaction
Add a new transaction to the blockchain.

**Usage:**
```bash
python -m cli.cli add-transaction <source> <recipient> <amount>
```

**Example:**
```bash
# Send 10.0 from Alice to Bob
python -m cli.cli add-transaction Alice Bob 10.0
```

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

Show the current balance of all users.

```bash
python -m cli.cli show-balances
```

### View Pending Transactions

Show transactions that are pending and not yet in a block.

```bash
python -m cli.cli show-pending
```

## Examples

1. **Create a simple transaction flow**:
   ```bash
      
   # Add some transactions
   python -m cli.cli add-transaction Alice Bob 10.0
   python -m cli.cli add-transaction Bob Charlie 5.0
   
   # View the blockchain
   python -m cli.cli show-chain

   # View a specific block (1-indexed)
   python -m cli.cli show-block 1
   
   # Check balances
   python -m cli.cli show-balances
   
   # View pending transactions
   python -m cli.cli show-pending

   # View invalid transactions
   python -m cli.cli show-invalid

   # Reset the blockchain
   python -m cli.cli reset
   ```

2. **Handle insufficient funds**:
   ```bash
   # This will fail if Alice doesn't have enough balance
   python -m cli.cli add-transaction Alice Bob 1000.0
   ```
