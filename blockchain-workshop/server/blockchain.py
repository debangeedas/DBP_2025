import hashlib
import json
from time import time
from typing import Dict, List, Optional
from datetime import datetime
from .transaction import Transaction

class Blockchain:
    def __init__(self):
        self.chain: List[Dict] = []
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {}
        self.invalid_transactions: List[Transaction] = []
        self.reset()

    def reset(self) -> None:
        """Reset the blockchain to its initial state with only the genesis block"""
        # Create genesis block
        genesis_block = {
            'index': 1,
            'timestamp': time(),
            'transactions': [],
            'previous_hash': '0' * 64,
            'hash': self._hash_block('genesis')
        }
        
        # Reset all state
        self.chain = [genesis_block]
        self.pending_transactions = []
        self.balances = {}
        self.invalid_transactions = []
        print("Blockchain reset complete: All transactions, balances, and history have been cleared.")

    def add_transaction(self, source: str, recipient: str, amount: float) -> bool:
        """Add a new transaction to the pending transactions list"""
        # Initialize balances for new users
        if source not in self.balances:
            self.balances[source] = 100.0  # Starting balance for new source
            print(f"New user '{source}' added with starting balance of $100.00")
        if recipient not in self.balances:
            self.balances[recipient] = 0.0  # Starting balance for new recipient
            print(f"New user '{recipient}' added with starting balance of $0.00")

        transaction = Transaction(source, recipient, amount)
        
        # Validate transaction
        if source == recipient:
            transaction.is_valid = False
            transaction.validation_error = "Source and recipient cannot be the same"
        elif amount <= 0:
            transaction.is_valid = False
            transaction.validation_error = f"Invalid amount: {amount}. Amount must be positive"
        elif self.balances[source] < amount:
            transaction.is_valid = False
            transaction.validation_error = f"Insufficient balance: {source} has ${self.balances[source]:.2f} but needs ${amount:.2f}"
        
        if not transaction.is_valid:
            self.invalid_transactions.append(transaction)
            print(f"\n=== INVALID TRANSACTION ===")
            print(f"From: {source}")
            print(f"To: {recipient}")
            print(f"Amount: ${amount:.2f}")
            print(f"Error: {transaction.validation_error}")
            print(f"Current balance of {source}: ${self.balances[source]:.2f}")
            print(f"Current balance of {recipient}: ${self.balances[recipient]:.2f}")
            print("===========================\n")
            return False

        # If we get here, the transaction is valid
        self.balances[source] -= amount
        self.balances[recipient] += amount
        self.pending_transactions.append(transaction)
        
        print(f"\n=== VALID TRANSACTION ===")
        print(f"From: {source} (${self.balances[source] + amount:.2f} -> ${self.balances[source]:.2f})")
        print(f"To: {recipient} (${self.balances[recipient] - amount:.2f} -> ${self.balances[recipient]:.2f})")
        print(f"Amount: ${amount:.2f}")
        print("======================\n")
        
        # Create a new block if we have 3 transactions
        if len(self.pending_transactions) >= 3:
            print("Creating new block...")
            self.create_block()
            
        return True

    def create_block(self) -> Dict:
        """Create a new block with pending transactions"""
        if not self.pending_transactions:
            return None

        block = {
            'index': len(self.chain) + 1,
            'timestamp': datetime.utcnow().isoformat(),
            'transactions': [transaction.to_dict() for transaction in self.pending_transactions],
            'previous_hash': self.get_latest_block_hash(),
            'hash': None
        }
        
        block['hash'] = self._hash_block(block)
        self.chain.append(block)
        self.pending_transactions = []
        
        return block

    def get_latest_block_hash(self) -> str:
        """Get the hash of the latest block in the chain"""
        if not self.chain:
            return "0" * 64  # Genesis block hash
        return self.chain[-1]['hash']

    def _hash_block(self, block: Dict) -> str:
        """Create a SHA-256 hash of a block"""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def get_balances(self) -> Dict[str, float]:
        """Get current balances of all users"""
        return self.balances

    def get_invalid_transactions(self) -> Dict[str, List[Dict]]:
        """Get all invalid transactions with their error messages"""
        return {
            'invalid_transactions': [{
                'source': tx.source,
                'recipient': tx.recipient,
                'amount': tx.amount,
                'timestamp': tx.timestamp,
                'validation_error': tx.validation_error
            } for tx in self.invalid_transactions]
        }
        
    def get_pending_transactions(self) -> List[Dict]:
        """Get all valid transactions that haven't been added to a block yet"""
        return [t.to_dict() for t in self.pending_transactions]

    def get_block(self, index: int) -> Optional[Dict]:
        """Get a block by its index (1-based)"""
        if 1 <= index <= len(self.chain):
            return self.chain[index - 1]
        return None

    def export_transactions_to_csv(self, filepath: str) -> bool:
        """This method is kept for compatibility but does nothing"""
        print("Export functionality has been removed")
        return False
