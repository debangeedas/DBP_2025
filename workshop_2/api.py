from flask import Flask, jsonify, request
import json
import logging
from typing import Dict, Any, Tuple

from blockchain import Blockchain, Transaction, Block
from node import Node

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api')

class BlockchainAPI:
    """REST API for interacting with the blockchain node."""
    
    def __init__(self, node: Node):
        """
        Initialize the API with a blockchain node.
        
        Args:
            node: The blockchain node to connect to the API
        """
        self.app = Flask(__name__)
        self.node = node
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self) -> None:
        """Register all API routes."""
        
        # Chain endpoints
        @self.app.route('/chain', methods=['GET'])
        def get_chain():
            chain_data = {
                'chain': [block.to_dict() for block in self.node.blockchain.chain],
                'length': len(self.node.blockchain.chain)
            }
            return jsonify(chain_data), 200
            
        @self.app.route('/chain/validate', methods=['GET'])
        def validate_chain():
            is_valid = self.node.blockchain.is_chain_valid()
            response = {
                'valid': is_valid,
                'length': len(self.node.blockchain.chain)
            }
            return jsonify(response), 200
            
        # Transaction endpoints
        @self.app.route('/transactions/new', methods=['POST'])
        def new_transaction():
            values = request.get_json()
            
            # Check required fields
            required_fields = ['sender', 'recipient', 'amount']
            if not all(field in values for field in required_fields):
                return jsonify({'message': 'Missing required fields'}), 400
                
            # Create transaction
            transaction = Transaction(
                sender=values['sender'],
                recipient=values['recipient'],
                amount=float(values['amount'])
            )
            
            # Check if this is a direct API call or forwarded from another node
            is_api_call = request.headers.get('X-Source-Type') != 'node_broadcast'
            
            # Log the source of the transaction
            if is_api_call:
                logger.info(f"Received new transaction via API: {transaction.sender} -> {transaction.recipient} ({transaction.amount})")
            else:
                logger.info(f"Received transaction from peer node: {transaction.sender} -> {transaction.recipient} ({transaction.amount})")
            
            # Add to blockchain - need to use the Transaction object not raw values
            success = self.node.blockchain.add_transaction(transaction)
            
            if success:
                # Only broadcast if this was from the API (not already a broadcast)
                if is_api_call:
                    logger.info("Broadcasting transaction to peer nodes")
                    self.node.broadcast_transaction(transaction)
                
                response = {'message': f'Transaction added to pool', 'transaction': transaction.to_dict()}
                return jsonify(response), 201
            else:
                response = {'message': 'Failed to add transaction', 'transaction': transaction.to_dict()}
                return jsonify(response), 400
                
        @self.app.route('/transactions/pending', methods=['GET'])
        def get_pending_transactions():
            transactions = [tx.to_dict() for tx in self.node.blockchain.pending_transactions]
            return jsonify({'transactions': transactions, 'count': len(transactions)}), 200
            
        @self.app.route('/transactions/rejected', methods=['GET'])
        def get_rejected_transactions():
            rejected = self.node.blockchain.get_rejected_transactions()
            return jsonify({'transactions': rejected, 'count': len(rejected)}), 200
            
        @self.app.route('/transactions/address/<address>', methods=['GET'])
        def get_address_transactions(address):
            transactions = self.node.blockchain.get_transactions_for_address(address)
            return jsonify({'transactions': transactions, 'count': len(transactions)}), 200
            
        # Block endpoints
        @self.app.route('/blocks/new', methods=['POST'])
        def new_block():
            values = request.get_json()
            
            try:
                # Check if this is from the API or forwarded from another node
                is_api_call = request.headers.get('X-Source-Type') != 'node_broadcast'
                
                # Log the source of the block
                block = Block.from_dict(values)
                if is_api_call:
                    logger.info(f"Received new block #{block.index} via API")
                else:
                    source_node = request.headers.get('X-Source-Node', 'unknown')
                    logger.info(f"Received block #{block.index} from peer node: {source_node}")
                
                # Process the block
                success = self.node.handle_new_block(values)
                
                if success:
                    # Log transaction removal for debugging
                    logger.info(f"Block #{block.index} added to chain, checking for pending transactions to remove")
                    
                    # Return success response
                    response = {'message': 'Block added to chain', 'block': values}
                    return jsonify(response), 201
                else:
                    response = {'message': 'Failed to add block', 'block': values}
                    return jsonify(response), 400
                    
            except Exception as e:
                logger.error(f"Error processing block: {str(e)}")
                response = {'message': f'Error processing block: {str(e)}'}
                return jsonify(response), 400
                
        @self.app.route('/blocks/<int:index>', methods=['GET'])
        def get_block(index):
            if index < 0 or index >= len(self.node.blockchain.chain):
                return jsonify({'message': 'Block not found'}), 404
                
            block = self.node.blockchain.chain[index]
            return jsonify(block.to_dict()), 200
            
        # Mining endpoints
        @self.app.route('/mine', methods=['GET'])
        def mine():
            # Check if node is a miner node
            if not self.node.miner_mode:
                return jsonify({'message': 'This node is not a miner node. Only miner nodes can mine blocks.'}), 403
                
            # Check if there are transactions to mine
            if not self.node.blockchain.pending_transactions:
                return jsonify({'message': 'No transactions to mine'}), 400
                
            # Mine a block
            block = self.node.blockchain.mine_pending_transactions(self.node.mining_address)
            
            # Broadcast the new block
            self.node.broadcast_block(block)
            
            response = {
                'message': 'New block mined',
                'block': block.to_dict()
            }
            return jsonify(response), 200
            
        @self.app.route('/mine/start', methods=['GET'])
        def start_mining():
            # Check if node is a miner node
            if not self.node.miner_mode:
                return jsonify({'message': 'This node is not a miner node. Only miner nodes can mine blocks.'}), 403
                
            # Start mining
            self.node.start_mining()
            
            return jsonify({'message': 'Mining started'}), 200
            
        @self.app.route('/mine/stop', methods=['GET'])
        def stop_mining():
            # Check if node is a miner node
            if not self.node.miner_mode:
                return jsonify({'message': 'This node is not a miner node. Only miner nodes can mine blocks.'}), 403
            
            self.node.stop_mining()
            return jsonify({'message': 'Mining stopped'}), 200
            
        # Node endpoints
        @self.app.route('/nodes/announce', methods=['POST'])
        def announce_node():
            values = request.get_json()
            
            if not values or not all(k in values for k in ['host', 'port', 'node_type']):
                return jsonify({'message': 'Error: Missing required node information'}), 400
                
            # Extract the announcing node's information
            host = values.get('host')
            port = values.get('port')
            node_type = values.get('node_type')
            name = values.get('name', f"Node {host}:{port}")
            active_nodes = values.get('active_nodes', [])
            
            # Record this node as active
            success = self.node.record_active_node(host, port, node_type, name)
            
            # Also record any active nodes that the announcing node knows about
            if active_nodes:
                for node_info in active_nodes:
                    if all(k in node_info for k in ['host', 'port', 'node_type']):
                        self.node.record_active_node(
                            node_info['host'],
                            node_info['port'],
                            node_info['node_type'],
                            node_info.get('name')
                        )
            
            # Prepare our response with our own node info and our known active nodes
            # This allows the announcing node to learn about us and our known active nodes
            our_info = {
                'host': self.node.host,
                'port': self.node.port,
                'node_type': 'miner' if self.node.miner_mode else 'full',
                'name': f"Node {self.node.host}:{self.node.port}",
                'active_nodes': self.node.get_active_nodes_info()
            }
            
            if success:
                response = {
                    'message': f'Node {host}:{port} recorded as active',
                    'node': our_info
                }
                return jsonify(response), 200
            else:
                response = {'message': f'Failed to record node {host}:{port}'}
                return jsonify(response), 500
        
        @self.app.route('/nodes/register', methods=['POST'])
        def register_nodes():
            values = request.get_json()
            
            if not values or 'nodes' not in values:
                return jsonify({'message': 'Error: Please supply a valid list of nodes'}), 400
                
            nodes = values['nodes']
            registered = 0
            
            for node_url in nodes:
                success = self.node.register_node(node_url)
                if success:
                    registered += 1
                    
            response = {
                'message': f'Registered {registered} new nodes',
                'total_nodes': len(self.node.registered_nodes)
            }
            return jsonify(response), 201
            
        @self.app.route('/nodes/peers', methods=['GET'])
        def get_peers():
            nodes = self.node.get_all_nodes()
            active_nodes = [node for node in nodes if node.get('active', False)]
            return jsonify({
                'nodes': nodes,
                'active_count': len(active_nodes),
                'total_count': len(nodes)
            }), 200
            
        @self.app.route('/nodes/resolve', methods=['GET'])
        def consensus():
            replaced = self.node.consensus()
            
            if replaced:
                response = {
                    'message': 'Chain was replaced',
                    'new_chain': [block.to_dict() for block in self.node.blockchain.chain]
                }
            else:
                response = {
                    'message': 'Our chain is authoritative',
                    'chain': [block.to_dict() for block in self.node.blockchain.chain]
                }
                
            return jsonify(response), 200
            
        @self.app.route('/nodes/info', methods=['GET'])
        def node_info():
            info = self.node.get_info()
            return jsonify(info), 200
            
        # Balance endpoints
        @self.app.route('/balance/<address>', methods=['GET'])
        def get_balance(address):
            balance = self.node.blockchain.get_balance(address)
            return jsonify({'address': address, 'balance': balance}), 200
            
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'message': 'Resource not found'}), 404
            
        @self.app.errorhandler(500)
        def server_error(error):
            return jsonify({'message': 'Server error'}), 500
            
    def start(self, host: str = '0.0.0.0', port: int = None, debug: bool = False) -> None:
        """
        Start the Flask server.
        
        Args:
            host: Host to run on
            port: Port to run on (defaults to node's port)
            debug: Whether to run in debug mode
        """
        port = port or self.node.port
        logger.info(f"Starting API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
        
    def get_app(self) -> Flask:
        """Get the Flask app instance."""
        return self.app
