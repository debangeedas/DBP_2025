import json
import requests
import time
import threading
import logging
import os
import uuid
from typing import List, Dict, Any, Set, Optional, Tuple
from urllib.parse import urlparse

from blockchain import Blockchain, Block, Transaction

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('node')

class Node:
    """
    Blockchain network node that handles peer discovery, 
    chain synchronization, and block/transaction propagation.
    """
    
    def __init__(self, host: str, port: int, blockchain: Optional[Blockchain] = None, 
                 miner_mode: bool = False, mining_interval: int = 30, config_file: str = 'nodes_config.json',
                 status_cache_time: int = 60, external_ip: str = None) -> None:
        """
        Initialize a blockchain node.
        
        Args:
            host: Host address to run on
            port: Port to run on
            blockchain: Existing blockchain or None to create new
            miner_mode: Whether to run as a miner
            mining_interval: Seconds between mining operations if in miner mode
            config_file: Path to the node configuration file
            status_cache_time: How long (in seconds) to cache node status before rechecking
            external_ip: The public/external IP address of this node (used for identification)
        """
        # Store the binding host separately from the identity host
        self.binding_host = host
        self.external_ip = external_ip
        
        # If binding to 0.0.0.0 but no external IP provided, try to detect it
        if host == '0.0.0.0' and not external_ip:
            try:
                # Try to auto-detect external IP - this will only work if the machine has internet access
                self.external_ip = self._detect_external_ip()
                logger.info(f"Auto-detected external IP: {self.external_ip}")
            except Exception as e:
                logger.warning(f"Could not auto-detect external IP: {e}")
                self.external_ip = None
        
        self.host = self._normalize_host(host)
        self.port = port
        self.node_address = str(uuid.uuid4()).replace('-', '')
        self.blockchain = blockchain or Blockchain()
        self.config_file = config_file
        self.registered_nodes = self._load_registered_nodes()
        self.miner_mode = miner_mode
        self.mining_interval = mining_interval
        self.mining_thread = None
        self.mining_address = f"miner-{self.node_address}"  # Address to receive mining rewards
        self.running = False
        
        # Track active nodes by their last announcement time
        self.active_nodes = {}  # Dictionary to store active node status: {node_id: last_announcement_time}
        self.activity_timeout = 300  # Consider a node inactive if we haven't heard from it in 5 minutes
        
        # Identity string for this node (used in logs and communication)
        self.node_identity = f"{self.host}:{self.port}"
        logger.info(f"Initialized node with identity: {self.node_identity}")
        if self.external_ip:
            logger.info(f"Node will identify using external IP: {self.external_ip}")
        
        # No longer needed for periodic announcements
        pass
        
    def _detect_external_ip(self) -> str:
        """Attempt to detect the external IP address of this node."""
        # Try several services to detect external IP
        ip_services = [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://ipinfo.io/ip"
        ]
        
        for service in ip_services:
            try:
                response = requests.get(service, timeout=3)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if ip and len(ip) < 45:  # Basic validation to ensure it looks like an IP
                        return ip
            except Exception as e:
                logger.debug(f"Failed to get IP from {service}: {e}")
                continue
                
        # If external detection fails, try to use a local interface IP
        try:
            # Get all non-loopback IPv4 addresses
            import socket
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            
            # Filter out loopback addresses
            external_ips = [ip for ip in ip_list if not ip.startswith('127.')]
            if external_ips:
                return external_ips[0]
        except Exception as e:
            logger.debug(f"Failed to get local IP: {e}")
            
        raise Exception("Could not detect external IP address")
    
    def _normalize_host(self, host: str) -> str:
        """Normalize host addresses for consistent identification."""
        # For binding purposes, 0.0.0.0 is used to listen on all interfaces
        # But for node identity, we need to use the actual external IP
        
        # Only normalize loopback addresses
        if host in ['localhost', '127.0.0.1']:
            return 'localhost'
        
        # 0.0.0.0 is a special case - when a node uses 0.0.0.0 for binding,
        # we should use its actual IP address for identification
        if host == '0.0.0.0' and hasattr(self, 'external_ip') and self.external_ip:
            return self.external_ip
            
        return host
        
    def _load_registered_nodes(self) -> List[Dict[str, Any]]:
        """Load registered nodes from configuration file."""
        if not os.path.exists(self.config_file):
            logger.warning(f"Configuration file {self.config_file} not found, creating default")
            node_type = "miner" if self.miner_mode else "full"
            default_config = {
                "nodes": [
                    {"host": "localhost", "port": 5000, "name": "Primary Node", "node_type": node_type}
                ]
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
                
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded {len(config.get('nodes', []))} registered nodes from config")
                return config.get('nodes', [])
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading config file: {e}")
            return []
            
    def _save_registered_nodes(self) -> bool:
        """Save registered nodes to configuration file."""
        try:
            config = {"nodes": self.registered_nodes}
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved {len(self.registered_nodes)} nodes to config")
            return True
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
            return False
        
    def _normalize_node_url(self, node_url: str) -> str:
        """Normalize node URLs for consistent identification."""
        parsed_url = urlparse(node_url)
        host = self._normalize_host(parsed_url.netloc.split(':')[0])
        port = parsed_url.netloc.split(':')[1] if ':' in parsed_url.netloc else '80'
        return f"http://{host}:{port}"
        
    def register_node(self, node_url: str) -> bool:
        """
        Register a new peer node in the configuration.
        
        Args:
            node_url: URL of the peer node
            
        Returns:
            bool: True if registration was successful
        """
        parsed_url = urlparse(node_url)
        host = self._normalize_host(parsed_url.netloc.split(':')[0])
        try:
            port = int(parsed_url.netloc.split(':')[1] if ':' in parsed_url.netloc else '80')
        except ValueError:
            logger.error(f"Invalid port in URL: {node_url}")
            return False
            
        # Don't register self
        if host == self.host and port == self.port:
            logger.warning("Cannot register self as peer")
            return False
            
        # Check if node is already registered
        for node in self.registered_nodes:
            if node.get('host') == host and node.get('port') == port:
                logger.info(f"Node {host}:{port} already registered")
                return True
                
        # Add new node to configuration
        new_node = {
            "host": host,
            "port": port,
            "name": f"Node {host}:{port}",
            "node_type": "unknown"  # We don't know its type yet
        }
        self.registered_nodes.append(new_node)
        success = self._save_registered_nodes()
        
        if success:
            logger.info(f"Registered new node: {host}:{port}")
        else:
            logger.error(f"Failed to save registration for node: {host}:{port}")
            
        return success
        
    def register_with_node(self, node_url: str) -> bool:
        """
        Register this node with another node to join the network.
        
        Args:
            node_url: URL of the existing node to register with
            
        Returns:
            bool: True if registration was successful
        """
        parsed_url = urlparse(node_url)
        host = self._normalize_host(parsed_url.netloc.split(':')[0])
        try:
            port = int(parsed_url.netloc.split(':')[1] if ':' in parsed_url.netloc else '80')
        except ValueError:
            logger.error(f"Invalid port in URL: {node_url}")
            return False
            
        # Don't register with self
        if host == self.host and port == self.port:
            logger.warning("Cannot register with self")
            return False
            
        # Check if the node is active before attempting to register
        if not self.check_node_status(host, port):
            logger.error(f"Node at {host}:{port} is not active")
            return False
            
        try:
            target_url = f"http://{host}:{port}"
            
            # Register with the other node
            response = requests.post(
                f"{target_url}/nodes/register",
                json={"nodes": [self.node_address]}
            )
            
            if response.status_code == 201:
                # Register the other node with self
                self.register_node(target_url)
                
                # Get all nodes from the other node
                response = requests.get(f"{target_url}/nodes/peers")
                if response.status_code == 200:
                    all_nodes = response.json().get('nodes', [])
                    
                    # Register nodes that aren't already in our config
                    for node_data in all_nodes:
                        if 'url' in node_data:
                            self.register_node(node_data['url'])
                        
                # Sync the blockchain
                self.consensus()
                logger.info(f"Successfully registered with node at {target_url}")
                return True
            else:
                logger.error(f"Failed to register with node {target_url}: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register with node {host}:{port}: {e}")
            
        return False
        
    def broadcast_transaction(self, transaction: Transaction) -> None:
        """
        Broadcast a transaction to all active peer nodes.
        
        Args:
            transaction: The transaction to broadcast
        """
        transaction_data = transaction.to_dict()
        
        # Get all active peer nodes with a forced status check to ensure we have current data
        active_nodes = self.get_active_nodes(exclude_self=True, force_check=True)
        
        if not active_nodes:
            logger.warning("No active peer nodes found to broadcast transaction to")
            return
            
        # Create headers that identify this as a node broadcast to prevent loops
        headers = {
            'Content-Type': 'application/json',
            'X-Source-Type': 'node_broadcast',
            'X-Source-Node': f"{self.host}:{self.port}"
        }
        
        logger.info(f"Broadcasting transaction from {transaction.sender} to {len(active_nodes)} peer nodes")
        
        successful_broadcasts = 0
        for node in active_nodes:
            node_url = node['url']
            try:
                response = requests.post(
                    f"{node_url}/transactions/new",
                    json=transaction_data,
                    headers=headers,
                    timeout=5.0  # Add timeout to prevent hanging
                )
                if response.status_code == 201:
                    successful_broadcasts += 1
                    logger.info(f"Successfully broadcast transaction to {node['name']} at {node_url}")
                else:
                    logger.warning(f"Failed to broadcast transaction to {node_url}, status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error broadcasting transaction to {node_url}: {e}")
                
        logger.info(f"Transaction broadcast complete: {successful_broadcasts} of {len(active_nodes)} peers received the transaction")
                
    def broadcast_block(self, block: Block) -> None:
        """
        Broadcast a newly mined block to all active peer nodes.
        
        Args:
            block: The block to broadcast
        """
        block_data = block.to_dict()
        
        # Force check active nodes to ensure we have current data
        active_nodes = self.get_active_nodes(exclude_self=True, force_check=True)
        
        if not active_nodes:
            logger.warning("No active peer nodes found to broadcast block to")
            return
            
        # Create headers that identify this as a node broadcast
        headers = {
            'Content-Type': 'application/json',
            'X-Source-Type': 'node_broadcast',
            'X-Source-Node': f"{self.host}:{self.port}"
        }
        
        logger.info(f"Broadcasting block #{block.index} to {len(active_nodes)} peer nodes")
        
        successful_broadcasts = 0
        for node in active_nodes:
            node_url = node['url']
            try:
                response = requests.post(
                    f"{node_url}/blocks/new",
                    json=block_data,
                    headers=headers,
                    timeout=5.0  # Add timeout to prevent hanging
                )
                if response.status_code == 201:
                    successful_broadcasts += 1
                    logger.info(f"Successfully broadcast block to {node['name']} at {node_url}")
                else:
                    logger.warning(f"Failed to broadcast block to {node_url}, status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error broadcasting block to {node_url}: {e}")
                
        logger.info(f"Block broadcast complete: {successful_broadcasts} of {len(active_nodes)} peers received the block")
                
    def consensus(self) -> bool:
        """
        Implement the consensus algorithm.
        Finds the longest valid chain among all active peers.
        
        Returns:
            bool: True if our chain was replaced, False otherwise
        """
        max_length = len(self.blockchain.chain)
        new_chain = None
        replaced = False
        active_nodes = self.get_active_nodes(exclude_self=True)
        
        logger.info(f"Running consensus with {len(active_nodes)} active peers")
        
        # Get chains from all active peers
        for node in active_nodes:
            node_url = node['url']
            try:
                response = requests.get(f"{node_url}/chain")
                
                if response.status_code == 200:
                    chain_data = response.json()
                    chain = chain_data.get('chain')
                    length = chain_data.get('length')
                    
                    # Check if chain is longer and valid
                    if length > max_length:
                        max_length = length
                        new_chain = chain
                        logger.info(f"Found longer chain ({length} blocks) from {node['name']}")
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to get chain from {node_url}: {e}")
                
        # Replace our chain if we found a longer valid one
        if new_chain:
            replaced = self.blockchain.replace_chain(new_chain)
            if replaced:
                logger.info(f"Chain replaced with longer chain ({max_length} blocks)")
            else:
                logger.warning("Longer chain was invalid, not replaced")
                
        return replaced
        
    # Periodic announcement methods removed as they are no longer needed
    
    def start_mining(self) -> None:
        """Start the backup mining process in a background thread.
        
        Note: This is now a backup mechanism. The primary mining trigger is the
        automatic detection of exactly 3 pending transactions in handle_new_transaction.
        This background thread serves as a failsafe.
        """
        if not self.miner_mode:
            logger.warning("Cannot start mining: node is not in miner mode")
            return
            
        if self.mining_thread and self.mining_thread.is_alive():
            logger.info("Background mining is already running")
            return
            
        self.running = True
        self.mining_thread = threading.Thread(target=self._mine_continuously)
        self.mining_thread.daemon = True
        self.mining_thread.start()
        logger.info(f"Started backup mining thread (checks every {self.mining_interval} seconds)")
        
    def stop_mining(self) -> None:
        """Stop the mining process."""
        self.running = False
        if self.mining_thread:
            self.mining_thread.join(timeout=1)
        logger.info("Stopped mining")
        
    def _mine_continuously(self) -> None:
        """Mine blocks continuously but only when we have exactly 3 non-system transactions."""
        while self.running:
            # Count only non-system transactions
            non_system_txs = [tx for tx in self.blockchain.pending_transactions if tx.sender != "0"]
            
            # Only mine if there are exactly 3 pending non-system transactions
            if len(non_system_txs) == 3:
                logger.info("Mining new block with 3 transactions...")
                block = self.blockchain.mine_pending_transactions(self.mining_address)
                self.broadcast_block(block)
                logger.info(f"Mined new block with index {block.index} containing 3 transactions")
            elif len(non_system_txs) > 0:
                # We have transactions but not enough to mine
                logger.info(f"Waiting for more transactions... Currently have {len(non_system_txs)}/3")
            else:
                logger.info("No pending transactions to mine")
                
            # Wait for the specified interval
            time.sleep(self.mining_interval)
            
    def handle_new_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Handle a new transaction received from a peer.
        
        Args:
            transaction_data: Dictionary representation of the transaction
            
        Returns:
            bool: True if transaction was added to the pool
        """
        try:
            transaction = Transaction.from_dict(transaction_data)
            
            # Don't broadcast received transactions - they've already been broadcast by the originating node
            # This prevents the cascade effect of each node re-broadcasting
            tx_hash = transaction.calculate_hash()
            
            # Pre-check if this is a duplicate before processing
            if self.blockchain._is_duplicate_transaction(transaction):
                logger.info(f"Transaction {tx_hash[:8]}... already exists, skipping")
                return False
                
            # Add transaction to our blockchain
            result = self.blockchain.add_transaction(transaction)
            
            # If transaction was added, check if we should mine
            if result and self.miner_mode and not self.mining_thread:
                # Count only non-system transactions (sender != "0")
                non_system_txs = [tx for tx in self.blockchain.pending_transactions if tx.sender != "0"]
                
                # Mine automatically when we have exactly 3 pending transactions
                if len(non_system_txs) == 3:
                    logger.info("Detected exactly 3 pending transactions - mining a new block")
                    # Mine immediately instead of starting the mining thread
                    new_block = self.blockchain.mine_pending_transactions(self.mining_address)
                    self.broadcast_block(new_block)
                    logger.info(f"Automatically mined block with index {new_block.index} containing 3 transactions")
                elif len(non_system_txs) > 3:
                    logger.warning(f"Have {len(non_system_txs)} pending transactions, more than the 3 transaction limit")
            elif not self.miner_mode:
                # Check if we have 3 transactions anyway so we can log a message
                non_system_txs = [tx for tx in self.blockchain.pending_transactions if tx.sender != "0"]
                if len(non_system_txs) == 3:
                    logger.warning("Have 3 pending transactions but this is not a miner node")
                    
            return result
            
        except Exception as e:
            logger.error(f"Failed to process transaction: {e}")
            return False
            
    def handle_new_block(self, block_data: Dict[str, Any]) -> bool:
        """
        Handle a new block received from a peer.
        
        Args:
            block_data: Dictionary representation of the block
            
        Returns:
            bool: True if the block was added to the chain
        """
        try:
            # Create a block from the received data
            block = Block.from_dict(block_data)
            
            # Get the latest block in our chain
            latest_block = self.blockchain.get_latest_block()
            
            # If this block is the next one in the chain
            if block.index == latest_block.index + 1 and block.previous_hash == latest_block.hash:
                # Validate the block
                if block.is_hash_valid():
                    # Add to our chain
                    self.blockchain.chain.append(block)
                    
                    # Update balances
                    self.blockchain._update_balances(block)
                    
                    # Remove transactions that are now in this block from our pending list
                    self._remove_transactions_in_block(block)
                    
                    logger.info(f"Added new block to chain: {block}")
                    return True
                    
            # If the block is part of a longer chain, perform consensus
            elif block.index > latest_block.index:
                self.consensus()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to process block: {e}")
            return False
            
    def _remove_transactions_in_block(self, block: Block) -> None:
        """
        Remove transactions that are in the block from our pending list.
        This ensures that transactions already included in a block are not processed again.
        
        Args:
            block: The block containing transactions to remove
        """
        # Log pending transactions before removal for debugging
        logger.info(f"Before removal: {len(self.blockchain.pending_transactions)} pending transactions")
        if self.blockchain.pending_transactions:
            for i, tx in enumerate(self.blockchain.pending_transactions):
                logger.info(f"  Pending tx #{i+1}: {tx.sender} -> {tx.recipient} ({tx.amount})")
        
        # Get transaction hashes from the block
        block_tx_hashes = {tx.calculate_hash() for tx in block.transactions}
        
        # Get transaction identifiers for more thorough matching
        block_tx_identifiers = {(tx.sender, tx.recipient, tx.amount) for tx in block.transactions}
        
        # Log transactions in the block
        logger.info(f"Block #{block.index} contains {len(block.transactions)} transactions:")
        for i, tx in enumerate(block.transactions):
            logger.info(f"  Block tx #{i+1}: {tx.sender} -> {tx.recipient} ({tx.amount})")
        
        # Get count before removal
        count_before = len(self.blockchain.pending_transactions)
        
        # First pass: Remove transactions with matching hashes
        transactions_after_hash_check = [
            tx for tx in self.blockchain.pending_transactions
            if tx.calculate_hash() not in block_tx_hashes
        ]
        
        # Second pass: Remove transactions with matching sender/recipient/amount
        # This is more aggressive and catches transactions that might have different timestamps
        self.blockchain.pending_transactions = [
            tx for tx in transactions_after_hash_check
            if (tx.sender, tx.recipient, tx.amount) not in block_tx_identifiers
        ]
        
        # Get count after removal
        count_after = len(self.blockchain.pending_transactions)
        removed = count_before - count_after
        
        # Log the result
        if removed > 0:
            logger.info(f"SUCCESS: Removed {removed} transactions from pending pool that are now in block {block.index}")
        else:
            logger.warning(f"WARNING: No pending transactions were removed for block {block.index}. This may indicate a synchronization issue.")
        
        # Log remaining transactions if any
        if self.blockchain.pending_transactions:
            logger.info(f"After removal: {len(self.blockchain.pending_transactions)} pending transactions remain:")
            for i, tx in enumerate(self.blockchain.pending_transactions):
                logger.info(f"  Remaining tx #{i+1}: {tx.sender} -> {tx.recipient} ({tx.amount})")
        else:
            logger.info("No pending transactions remain after block processing")
        
    def record_active_node(self, host: str, port: int, node_type: str, name: str = None) -> bool:
        """Record a node as active based on its announcement.
        
        Args:
            host: Host address of the node
            port: Port number of the node
            node_type: Type of node ('full' or 'miner')
            name: Optional name for the node
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate a unique key for this node
            node_key = f"{host}:{port}"
            
            # Update the active nodes dictionary with current timestamp
            self.active_nodes[node_key] = time.time()
            
            # Check if this node is already in our registered nodes
            for node in self.registered_nodes:
                if node.get('host') == host and node.get('port') == port:
                    # Update existing node's info
                    node['node_type'] = node_type
                    if name:
                        node['name'] = name
                    # Save the updated configuration
                    self._save_registered_nodes()
                    logger.info(f"Updated node {host}:{port} status to active")
                    return True
            
            # Node not found in registered nodes, add it
            new_node = {
                "host": host,
                "port": port,
                "name": name or f"Node {host}:{port}",
                "node_type": node_type
            }
            self.registered_nodes.append(new_node)
            self._save_registered_nodes()
            logger.info(f"Added new active node {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording active node {host}:{port}: {e}")
            return False
    
    def check_node_status(self, host: str, port: int, timeout: float = 2.0, force_check: bool = False) -> bool:
        """
        Check if a node is active based on its last announcement time.
        If force_check is True, we'll also try to ping the node's API.
        
        Args:
            host: Host address
            port: Port number
            timeout: Timeout for API requests if force_check is True
            force_check: Whether to force an API check even if the node appears inactive
            
        Returns:
            bool: True if node is active, False otherwise
        """
        # Generate a unique key for this node
        node_key = f"{host}:{port}"
        
        # If this is our own node, always return True
        if host == self.host and port == self.port:
            return True
        
        current_time = time.time()
        
        # Check if we have an announcement record for this node
        if node_key in self.active_nodes:
            last_announcement = self.active_nodes[node_key]
            
            # Node is active if we've heard from it within the activity timeout period
            if (current_time - last_announcement) < self.activity_timeout:
                return True
                
        # No recent announcement record found or node appears inactive
        # If force_check is True, try to ping the node's API
        if force_check:
            try:
                node_url = f"http://{host}:{port}"
                response = requests.get(f"{node_url}/nodes/info", timeout=timeout)
                if response.status_code == 200:
                    # Node is responsive, update its active status
                    self.active_nodes[node_key] = current_time
                    logger.info(f"Node {host}:{port} is active through direct ping")
                    return True
            except requests.exceptions.RequestException:
                # Failed to connect, node is inactive
                pass
                
        return False
            
    def get_active_nodes_info(self) -> List[Dict[str, Any]]:
        """Get basic information about active nodes for sharing with peers.
        
        Returns:
            List of dictionaries containing basic node information for active nodes
        """
        active_nodes_info = []
        current_time = time.time()
        
        for node in self.registered_nodes:
            host = node.get('host')
            port = node.get('port')
            node_key = f"{host}:{port}"
            
            # Check if this node is active based on announcement time
            if node_key in self.active_nodes:
                last_announcement = self.active_nodes[node_key]
                if (current_time - last_announcement) < self.activity_timeout:
                    # Only include essential information for propagation
                    active_nodes_info.append({
                        'host': host,
                        'port': port,
                        'node_type': node.get('node_type', 'full'),
                        'name': node.get('name', f"Node {host}:{port}")
                    })
                    
        return active_nodes_info
    
    def get_active_nodes(self, exclude_self: bool = False, force_check: bool = True) -> List[Dict[str, Any]]:
        """Get all active registered nodes.
        
        Args:
            exclude_self: Whether to exclude this node from the results
            force_check: Whether to force a direct API check to confirm node status
            
        Returns:
            List of dictionaries containing node information
        """
        active_nodes = []
        
        # If we have no registered nodes, log a warning
        if not self.registered_nodes:
            logger.warning("No registered nodes found to check for activity")
            return active_nodes
            
        logger.info(f"Checking status of {len(self.registered_nodes)} registered nodes (force_check={force_check})")
        
        for node in self.registered_nodes:
            host = node.get('host')
            port = node.get('port')
            
            # Skip self if requested
            if exclude_self and host == self.host and port == self.port:
                continue
                
            # Check node status with optional force check
            is_active = self.check_node_status(host, port, force_check=force_check)
            
            if is_active:
                node_info = node.copy()
                node_info['active'] = True
                node_info['url'] = f"http://{host}:{port}"
                active_nodes.append(node_info)
                
        logger.info(f"Found {len(active_nodes)} active nodes out of {len(self.registered_nodes)} registered nodes")
        return active_nodes
        
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all registered nodes with their active status."""
        nodes_with_status = []
        
        for node in self.registered_nodes:
            host = node.get('host')
            port = node.get('port')
            
            # Check if node is active
            is_active = self.check_node_status(host, port)
            
            node_info = node.copy()
            node_info['active'] = is_active
            node_info['url'] = f"http://{host}:{port}"
            nodes_with_status.append(node_info)
            
        return nodes_with_status
        
    def get_peers(self) -> List[Dict[str, Any]]:
        """Get the list of peer nodes with status."""
        return self.get_all_nodes()
        
    def announce_to_peers(self) -> int:
        """Announce this node to all registered peers and collect their activity information.
        
        Returns:
            int: Number of successful announcements
        """
        # Mark ourselves as active
        self.active_nodes[f"{self.host}:{self.port}"] = time.time()
        
        # Get our current active nodes to share with peers
        active_nodes_info = self.get_active_nodes_info()
        
        # Prepare announcement data
        announcement = {
            'host': self.host,
            'port': self.port,
            'node_type': 'miner' if self.miner_mode else 'full',
            'name': f"Node {self.host}:{self.port}",
            'active_nodes': active_nodes_info  # Share our knowledge of active nodes
        }
        
        successful_announcements = 0
        
        # Announce to all registered peers (except self)
        for node in self.registered_nodes:
            host = node.get('host')
            port = node.get('port')
            
            # Skip announcing to self
            if host == self.host and port == self.port:
                continue
                
            try:
                url = f"http://{host}:{port}/nodes/announce"
                response = requests.post(url, json=announcement, timeout=2.0)
                
                if response.status_code == 200:
                    successful_announcements += 1
                    logger.info(f"Successfully announced to {host}:{port}")
                    
                    # Process the response to learn about the responding node and its active nodes
                    response_data = response.json()
                    if 'node' in response_data:
                        node_info = response_data['node']
                        
                        # Record the responding node as active
                        if all(k in node_info for k in ['host', 'port', 'node_type']):
                            self.record_active_node(
                                node_info['host'], 
                                node_info['port'], 
                                node_info['node_type'],
                                node_info.get('name')
                            )
                            
                        # Process active nodes from the response
                        if 'active_nodes' in node_info and isinstance(node_info['active_nodes'], list):
                            for active_node in node_info['active_nodes']:
                                if all(k in active_node for k in ['host', 'port', 'node_type']):
                                    self.record_active_node(
                                        active_node['host'],
                                        active_node['port'],
                                        active_node['node_type'],
                                        active_node.get('name')
                                    )
                else:
                    logger.warning(f"Failed to announce to {host}:{port}: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to announce to {host}:{port}: {e}")
                
        logger.info(f"Announced to {successful_announcements} peers")
        return successful_announcements
    
    def get_info(self) -> Dict[str, Any]:
        """Get node information."""
        active_nodes = self.get_active_nodes(exclude_self=True)
        return {
            'address': self.node_address,
            'host': self.host,
            'port': self.port,
            'node_type': 'miner' if self.miner_mode else 'full',
            'registered_nodes': len(self.registered_nodes),
            'active_nodes': len(active_nodes),
            'chain_length': len(self.blockchain.chain),
            'pending_transactions': len(self.blockchain.pending_transactions),
            'is_mining': self.mining_thread is not None and self.mining_thread.is_alive() if self.mining_thread else False,
            'miner_mode': self.miner_mode
        }
