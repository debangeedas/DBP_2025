# Simple Blockchain Network - Beginner's Guide

Welcome to your very own blockchain network! This guide will help you set up and run a simple blockchain on your computer - no technical knowledge required.

## What Is This?

This is a simple blockchain network that you can run on your own computer. Think of it like a digital ledger where you can record transactions between users and everyone in the network can see and verify these transactions.

### What You Can Do

- Create a network of connected computers (nodes)
- Send digital money between users
- Watch transactions get processed and added to blocks
- See how mining works in real-time
- Check account balances at any time

## Two Types of Nodes in Our Network

### 1. Full Node

A full node in our network:
- Keeps track of all transactions
- Verifies that transactions are valid
- Maintains a copy of the entire transaction history
- CANNOT create new blocks (mining)

### 2. Miner Node

A miner node does everything a full node does, PLUS:
- Collects transactions into blocks
- Automatically mines new blocks when 3 transactions are ready
- Gets rewards for creating new blocks

## Getting Started

### Step 1: Start Your First Node

Let's start with a full node:

```
python main.py --host 0.0.0.0 --port 5000 --node-type full --cli
```

This starts a full node on your computer with a command-line interface so you can interact with it.

### Step 2: Start a Mining Node

Open a new command prompt or terminal window and run:

```
python main.py --host 0.0.0.0 --port 5001 --node-type miner --peer http://127.0.0.1:5000 --cli
```

This starts a mining computer that connects to your first node and can create new blocks.

## How Mining Works

### Automatic Block Creation

In our blockchain network, new blocks are created automatically when:

1. **Three Transactions Rule**: A mining computer will automatically create a new block once it has exactly 3 transactions ready
2. **Starting Money**: When someone makes their first transaction, they automatically get 100 digital coins
3. **Real-time Balance Updates**: Your account balance updates immediately after each transaction

## Using the Command Line Interface

After starting a node with the `--cli` flag, you'll see a prompt where you can type commands:

### Commands

- `help` - Shows all available commands
- `transaction <from> <to> <amount>` - Send money from one person to another
  - Example: `transaction Alice Bob 10` sends 10 coins from Alice to Bob
- `pending` - See transactions waiting to be processed
- `chain` - View the entire blockchain (all blocks and transactions)
- `peers` - See all computers connected to your network
- `block <number>` - View details of a specific block
- `history <name>` - See all transactions for a specific person
- `balance <name>` - Check how much money someone has
  - Example: `balance Alice` shows Alice's current balance

## Security Features

Our blockchain automatically:
- Verifies all transactions are valid (sender has enough money)
- Prevents duplicate transactions
- Keeps all computers in sync with the same data
- Secures blocks using advanced cryptography
