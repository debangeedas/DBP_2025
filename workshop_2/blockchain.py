import hashlib
import json
import time
from typing import List, Dict, Any, Optional
import uuid
import logging
from Crypto.Hash import SHA256

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('blockchain')

class Transaction:
    """Represents a financial transaction on the blockchain."""
    
    def __init__(self, sender: str, recipient: str, amount: float, timestamp: Optional[float] = None, signature: str = None):
        """
        Initialize a new transaction.
        
        Args:
            sender: The address of the sender
            recipient: The address of the recipient
            amount: The amount to transfer
            timestamp: Transaction time (defaults to current time)
            signature: Optional transaction signature for future use
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.signature = signature or str(uuid.uuid4())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary format."""
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'signature': self.signature
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create a Transaction object from a dictionary."""
        return cls(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=data['amount'],
            timestamp=data['timestamp'],
            signature=data['signature']
        )
        
    def calculate_hash(self) -> str:
        """Calculate a hash of the transaction."""
        transaction_string = json.dumps(self.to_dict(), sort_keys=True)
        return SHA256.new(transaction_string.encode()).hexdigest()
        
    def __eq__(self, other):
        """Compare transactions by their hash."""
        if not isinstance(other, Transaction):
            return False
        return self.calculate_hash() == other.calculate_hash()
        
    def __repr__(self):
        return f"Transaction(sender={self.sender}, recipient={self.recipient}, amount={self.amount})"


class Block:
    """Represents a block in the blockchain."""
    
    def __init__(self, index: int, transactions: List[Transaction], timestamp: float, 
                 previous_hash: str, nonce: int = 0, difficulty: int = 4):
        """
        Initialize a new block.
        
        Args:
            index: Block index in the chain
            transactions: List of transactions in this block
            timestamp: Block creation time
            previous_hash: Hash of the previous block
            nonce: Proof-of-work nonce
            difficulty: Mining difficulty (number of leading zeros required)
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.difficulty = difficulty
        self.hash = self.calculate_hash()
        
    def calculate_hash(self) -> str:
        """Calculate the hash of the block."""
        block_string = json.dumps({
            'index': self.index,
            'transactions': [t.to_dict() for t in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
        
    def mine_block(self) -> None:
        """
        Mine the block by finding a hash with the required difficulty.
        This implements Proof of Work consensus mechanism.
        """
        target = '0' * self.difficulty
        
        while self.hash[:self.difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            
        logger.info(f"Block mined: {self.hash}")
        
    def is_hash_valid(self) -> bool:
        """Verify that the block's hash meets the difficulty requirement."""
        return (self.hash[:self.difficulty] == '0' * self.difficulty and
                self.hash == self.calculate_hash())
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert the block to a dictionary."""
        return {
            'index': self.index,
            'transactions': [t.to_dict() for t in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'hash': self.hash
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """Create a Block object from a dictionary."""
        transactions = [Transaction.from_dict(t) for t in data['transactions']]
        block = cls(
            index=data['index'],
            transactions=transactions,
            timestamp=data['timestamp'],
            previous_hash=data['previous_hash'],
            nonce=data['nonce'],
            difficulty=data['difficulty']
        )
        block.hash = data['hash']
        return block
        
    def __repr__(self):
        return f"Block(index={self.index}, hash={self.hash}, tx_count={len(self.transactions)})"


class Blockchain:
    """The main blockchain class."""
    
    def __init__(self, difficulty: int = 4):
        """
        Initialize a new blockchain.
        
        Args:
            difficulty: The PoW mining difficulty
        """
        # Initialize with genesis block
        self.chain = []
        self.pending_transactions = []
        self.rejected_transactions = []
        self.difficulty = difficulty
        self.user_balances = {}  # User -> balance mapping
        self.mining_reward = 1.0  # Reward for mining a block
        
        # Create the genesis block
        self.create_genesis_block()
        
    def create_genesis_block(self) -> None:
        """Create the first block in the chain (genesis block)."""
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        logger.info("Genesis block created")
        
    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain."""
        return self.chain[-1]
        
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a transaction to the pending transactions pool.
        
        Args:
            transaction: The transaction to add
            
        Returns:
            bool: True if transaction is valid and added, False otherwise
        """
        # Check if transaction already exists in pending or in the chain
        if self._is_duplicate_transaction(transaction):
            logger.warning(f"Rejected duplicate transaction: {transaction}")
            self._reject_transaction(transaction, "Duplicate transaction")
            return False
            
        # Validate transaction (sufficient funds)
        if not self._is_transaction_valid(transaction):
            logger.warning(f"Rejected invalid transaction: {transaction}")
            self._reject_transaction(transaction, "Insufficient funds")
            return False
            
        # Add to pending transactions
        self.pending_transactions.append(transaction)
        logger.info(f"Transaction added to pool: {transaction}")
        
        # Return True and indicate if we've reached 3 transactions
        # Don't count system transactions (sender="0") in this count
        non_system_transactions = [tx for tx in self.pending_transactions if tx.sender != "0"]
        reached_transaction_limit = len(non_system_transactions) >= 3
        
        logger.info(f"Current pending transactions: {len(non_system_transactions)} (non-system)")
        if reached_transaction_limit:
            logger.info("Reached 3 pending transactions, ready for mining")
            
        return True
        
    def _is_duplicate_transaction(self, transaction: Transaction) -> bool:
        """Check if a transaction is a duplicate by comparing transaction hashes."""
        # Generate hash for this transaction
        tx_hash = transaction.calculate_hash()
        
        # Check pending transactions by hash
        for tx in self.pending_transactions:
            if tx.calculate_hash() == tx_hash:
                logger.info(f"Rejecting duplicate transaction: {transaction}")
                return True
                
        # Check transactions in blockchain by hash
        for block in self.chain:
            for tx in block.transactions:
                if tx.calculate_hash() == tx_hash:
                    logger.info(f"Rejecting duplicate transaction: already in blockchain")
                    return True
                    
        # Also check for transactions between same parties with same amount
        # (common user mistake of clicking submit twice)
        for tx in self.pending_transactions:
            if (tx.sender == transaction.sender and 
                tx.recipient == transaction.recipient and 
                tx.amount == transaction.amount):
                # Very likely a duplicate submission
                logger.info(f"Rejecting likely duplicate transaction between same parties with same amount")
                return True
                    
        return False
        
    def _is_transaction_valid(self, transaction: Transaction) -> bool:
        """
        Validate a transaction.
        
        A transaction is valid if:
        - It's a mining reward (sender is "0")
        - The sender has sufficient funds (or it's their first transaction, they get 100 initial balance)
        """
        # Mining rewards are always valid
        if transaction.sender == "0":
            return True
            
        # Check if sender exists in user_balances
        if transaction.sender not in self.user_balances:
            # First transaction for this user - initialize with 100 balance
            logger.info(f"Initializing new user {transaction.sender} with 100 balance")
            self.user_balances[transaction.sender] = 100.0
            
        # Check if recipient exists in user_balances
        if transaction.recipient not in self.user_balances:
            # First transaction for this recipient - initialize with 0 balance
            logger.info(f"Initializing new user {transaction.recipient} with 0 balance")
            self.user_balances[transaction.recipient] = 0.0
            
        # Check if sender has enough funds
        sender_balance = self.user_balances[transaction.sender]
        
        if sender_balance < transaction.amount:
            self._reject_transaction(transaction, f"Insufficient funds: {sender_balance} < {transaction.amount}")
            return False
        
        # Update balances immediately after validation for real-time balance tracking
        self.user_balances[transaction.sender] -= transaction.amount
        self.user_balances[transaction.recipient] += transaction.amount
        logger.info(f"Updated balance for {transaction.sender}: {self.user_balances[transaction.sender]}")
        logger.info(f"Updated balance for {transaction.recipient}: {self.user_balances[transaction.recipient]}")
            
        return True
        
    def _reject_transaction(self, transaction: Transaction, reason: str) -> None:
        """Add a transaction to the rejected list with reason."""
        self.rejected_transactions.append({
            'transaction': transaction.to_dict(),
            'reason': reason,
            'timestamp': time.time()
        })
        
    def mine_pending_transactions(self, miner_address: str) -> Block:
        """
        Mine a new block with all pending transactions.
        
        Args:
            miner_address: Address to receive the mining reward
            
        Returns:
            The newly mined block
        """
        # First, add a mining reward transaction
        reward_transaction = Transaction(
            sender="0",  # "0" signifies a system reward
            recipient=miner_address,
            amount=self.mining_reward
        )
        self.pending_transactions.append(reward_transaction)
        
        # Create a new block
        block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions,
            timestamp=time.time(),
            previous_hash=self.get_latest_block().hash,
            difficulty=self.difficulty
        )
        
        # Mine the block
        block.mine_block()
        
        # Add to the chain
        self.chain.append(block)
        
        # Update balances
        self._update_balances(block)
        
        # Clear pending transactions
        self.pending_transactions = []
        
        logger.info(f"Block mined and added to chain: {block}")
        return block
        
    def _update_balances(self, block: Block) -> None:
        """Update account balances based on a block's transactions."""
        # Note: Most balance updates happen in real-time during transaction validation
        # This method is mainly for processing mining rewards and for blockchain reconstruction
        
        for transaction in block.transactions:
            # Skip if sender is 0 (mining reward)
            if transaction.sender == "0":
                # Only handle mining rewards here
                if transaction.recipient in self.user_balances:
                    self.user_balances[transaction.recipient] += transaction.amount
                    logger.info(f"Mining reward: {transaction.recipient} balance updated to {self.user_balances[transaction.recipient]}")
                else:
                    self.user_balances[transaction.recipient] = transaction.amount
                    logger.info(f"Mining reward: {transaction.recipient} initialized with {transaction.amount}")
            # Regular transactions are already processed during validation
            # This handles transactions when reconstructing the blockchain from storage
            
    def get_balance(self, address: str) -> float:
        """Get the current balance for an address."""
        if address not in self.user_balances:
            return 0
        return self.user_balances[address]
        
    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain.
        
        Checks:
        1. Each block's hash is correct
        2. Each block points to the correct previous hash
        3. Each block's hash meets the difficulty requirement
        4. Each transaction is valid (has sufficient funds)
        
        Returns:
            bool: True if the chain is valid, False otherwise
        """
        # Check if chain is empty or just the genesis block
        if not self.chain or len(self.chain) == 1:
            return True
            
        # Start from the second block (index 1) since genesis is always valid
        temp_user_balances = {}  # Track user balances during validation
        
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check hash integrity
            if current_block.hash != current_block.calculate_hash():
                logger.warning(f"Invalid hash in block {i}")
                return False
                
            # Check previous hash link
            if current_block.previous_hash != previous_block.hash:
                logger.warning(f"Invalid previous_hash in block {i}")
                return False
                
            # Check proof-of-work
            if not current_block.is_hash_valid():
                logger.warning(f"Invalid proof-of-work in block {i}")
                return False
                
            # Verify each transaction
            for tx in current_block.transactions:
                # Initialize balances for new users with proper starting amounts
                if tx.sender not in temp_user_balances and tx.sender != "0":
                    # New senders start with 100 balance
                    temp_user_balances[tx.sender] = 100.0
                    
                if tx.recipient not in temp_user_balances:
                    # New recipients start with 0 balance
                    temp_user_balances[tx.recipient] = 0.0
                
                # Skip mining rewards
                if tx.sender == "0":
                    # Just add the mining reward to recipient
                    temp_user_balances[tx.recipient] += tx.amount
                    continue
                    
                # Check if sender has enough funds
                if temp_user_balances[tx.sender] < tx.amount:
                    logger.warning(f"Invalid chain: Transaction in block {i} has insufficient funds")
                    return False
                    
                # Update temporary balances
                temp_user_balances[tx.sender] -= tx.amount
                temp_user_balances[tx.recipient] += tx.amount
                
        return True
        
    def replace_chain(self, new_chain: List[Dict[str, Any]]) -> bool:
        """
        Replace the chain with a new one if it's longer and valid.
        Implements the longest chain rule.
        
        Args:
            new_chain: The new chain in dictionary format
            
        Returns:
            bool: True if chain was replaced, False otherwise
        """
        # Convert the dict chain to Block objects
        blocks = [Block.from_dict(block_data) for block_data in new_chain]
        
        # Check if the new chain is longer and valid
        if len(blocks) <= len(self.chain):
            logger.info("Received chain is not longer than current chain")
            return False
            
        # Validate the new chain
        temp_blockchain = Blockchain()
        temp_blockchain.chain = blocks
        
        if not temp_blockchain.is_chain_valid():
            logger.warning("Received chain is invalid")
            return False
            
        # Store the current pending transactions
        original_pending = self.pending_transactions.copy()
        
        # Replace chain and update balances
        self.chain = blocks
        
        # Recalculate all balances
        self.user_balances = {}
        for block in self.chain:
            self._update_balances(block)
            
        # Clean pending transactions - remove any that are already in the new chain
        all_transactions_in_chain = []
        for block in self.chain:
            all_transactions_in_chain.extend(block.transactions)
            
        # Create sets of transaction identifiers in the chain
        tx_hashes_in_chain = {tx.calculate_hash() for tx in all_transactions_in_chain}
        tx_details_in_chain = {(tx.sender, tx.recipient, tx.amount) for tx in all_transactions_in_chain}
        
        # Filter pending transactions to keep only those not in the chain
        self.pending_transactions = [
            tx for tx in original_pending
            if (tx.calculate_hash() not in tx_hashes_in_chain and 
                (tx.sender, tx.recipient, tx.amount) not in tx_details_in_chain)
        ]
        
        removed_count = len(original_pending) - len(self.pending_transactions)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} transactions from pending pool that were already in the new chain")
            
        logger.info("Blockchain replaced with a longer valid chain")
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the blockchain to a dictionary for serialization."""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'difficulty': self.difficulty
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Blockchain':
        """Create a Blockchain object from a dictionary."""
        blockchain = cls(difficulty=data['difficulty'])
        blockchain.chain = [Block.from_dict(block_data) for block_data in data['chain']]
        blockchain.pending_transactions = [Transaction.from_dict(tx_data) 
                                          for tx_data in data['pending_transactions']]
        
        # Recalculate user balances
        blockchain.user_balances = {}
        for block in blockchain.chain:
            blockchain._update_balances(block)
            
        return blockchain
        
    def get_transactions_for_address(self, address: str) -> List[Dict[str, Any]]:
        """Get all transactions involving a specific address."""
        transactions = []
        
        # Check the chain
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    transactions.append({
                        'transaction': tx.to_dict(),
                        'block_index': block.index,
                        'block_hash': block.hash
                    })
                    
        return transactions
        
    def get_rejected_transactions(self) -> List[Dict[str, Any]]:
        """Get all rejected transactions."""
        return self.rejected_transactions
