from flask import Flask, jsonify, request
from .blockchain import Blockchain
from .transaction import Transaction

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required = ['source', 'recipient', 'amount']
    
    if not all(k in data for k in required):
        return 'Missing values', 400
    
    success = blockchain.add_transaction(
        source=data['source'],
        recipient=data['recipient'],
        amount=float(data['amount'])
    )
    
    if not success:
        # Find the last invalid transaction and return its error message
        if blockchain.invalid_transactions:
            last_tx = blockchain.invalid_transactions[-1]
            error_msg = last_tx.validation_error
            return jsonify({
                'error': 'Invalid transaction',
                'reason': error_msg
            }), 400
        else:
            return 'Invalid transaction (unknown reason)', 400
    
    return 'Transaction added successfully', 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/block/<int:index>', methods=['GET'])
def get_block(index):
    block = blockchain.get_block(index)
    if block is None:
        return 'Block not found', 404
    return jsonify(block), 200

@app.route('/balances', methods=['GET'])
def get_balances():
    return jsonify(blockchain.get_balances()), 200

@app.route('/invalid', methods=['GET'])
def get_invalid_transactions():
    """Get all invalid transactions"""
    return jsonify(blockchain.get_invalid_transactions()), 200

@app.route('/pending', methods=['GET'])
def get_pending_transactions():
    """Get all valid transactions waiting to be added to a block"""
    return jsonify(blockchain.get_pending_transactions()), 200

@app.route('/reset', methods=['POST'])
def reset():
    # Reset the blockchain
    blockchain.reset()
    print("Blockchain reset to genesis block")
    return 'Blockchain reset successfully', 200

@app.route('/export', methods=['POST'])
def export_blockchain():
    data = request.get_json()
    if not data or 'filepath' not in data:
        return jsonify({'error': 'Filepath is required'}), 400
        
    filepath = data['filepath']
    
    # Ensure the filepath is valid and has proper extension
    if not filepath.endswith('.json'):
        filepath += '.json'
        
    success = blockchain.export_blockchain(filepath)
    
    if success:
        return jsonify({
            'success': True,
            'message': f'Blockchain data exported successfully to {filepath}',
            'filepath': filepath
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': f'Failed to export blockchain data to {filepath}'
        }), 500

@app.route('/users/create', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'username' not in data:
        return 'Username is required', 400
        
    username = data['username']
    if not username or not isinstance(username, str):
        return 'Username must be a non-empty string', 400
        
    if blockchain.create_user(username):
        return 'User created successfully', 201
    else:
        return 'Failed to create user. User may already exist.', 400

def load_transactions_from_csv():
    """This function is kept for compatibility but returns an empty list"""
    print("File I/O has been disabled. Starting with an empty blockchain.")
    return []

def run_server(port=5000):
    """Run the Flask server"""
    global blockchain
    
    # Initialize empty blockchain
    blockchain = Blockchain()
    print("Initialized new empty blockchain")
    print("Current balances:", blockchain.balances)
    
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    run_server()
