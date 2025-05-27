import argparse
import json
import sys
import time
import logging
import requests
from typing import Dict, Any, List, Optional
import uuid

from blockchain import Transaction

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('cli')

class BlockchainCLI:
    """Command-line interface for the blockchain network."""
    
    def __init__(self, node_address: str):
        """
        Initialize the CLI with a node address to connect to.
        
        Args:
            node_address: The address of the node to connect to (http://host:port)
        """
        self.node_address = node_address
        self.commands = {
            'help': self.show_help,
            'info': self.show_node_info,
            'chain': self.show_chain,
            'validate': self.validate_chain,
            'balance': self.show_balance,
            'transaction': self.create_transaction,
            'pending': self.show_pending_transactions,
            'rejected': self.show_rejected_transactions,
            'mine': self.mine_block,
            'mining': {
                'start': self.start_mining,
                'stop': self.stop_mining
            },
            'peers': self.show_peers,
            'register': self.register_node,
            'consensus': self.run_consensus,
            'block': self.show_block,
            'history': self.show_transaction_history,
            'exit': self.exit_cli
        }
        
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the node API.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method (GET, POST)
            data: Data to send in the request
            
        Returns:
            Dictionary of response data
        """
        url = f"{self.node_address}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url)
            elif method == 'POST':
                response = requests.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {'error': str(e)}
            
    def show_help(self, *args) -> None:
        """Show available commands."""
        print("\nAvailable Commands:")
        print("------------------")
        print("help                   - Show this help message")
        print("info                   - Show node information")
        print("chain                  - Show the blockchain")
        print("validate               - Validate the blockchain")
        print("balance <address>      - Show balance for an address")
        print("transaction <from> <to> <amount> - Create a new transaction")
        print("pending                - Show pending transactions")
        print("rejected               - Show rejected transactions")
        print("mine                   - Mine a new block")
        print("mining start           - Start continuous mining")
        print("mining stop            - Stop continuous mining")
        print("peers                  - Show connected peers")
        print("register <url>         - Register a new peer node")
        print("consensus              - Run the consensus algorithm")
        print("block <index>          - Show block details")
        print("history <address>      - Show transaction history for an address")
        print("exit                   - Exit the CLI")
        
    def show_node_info(self, *args) -> None:
        """Show information about the connected node."""
        response = self._make_request('nodes/info')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        print("\nNode Information:")
        print("-----------------")
        print(f"Address: {response.get('address', 'Unknown')}")
        print(f"Host: {response.get('host', 'Unknown')}")
        print(f"Port: {response.get('port', 'Unknown')}")
        print(f"Node Type: {response.get('node_type', 'Unknown').upper()}")
        print(f"Registered Nodes: {response.get('registered_nodes', 0)}")
        print(f"Active Nodes: {response.get('active_nodes', 0)}")
        print(f"Chain Length: {response.get('chain_length', 0)}")
        print(f"Pending Transactions: {response.get('pending_transactions', 0)}")
        print(f"Mining Status: {'Running' if response.get('is_mining', False) else 'Stopped'}")
        print(f"Mining Mode: {'Enabled' if response.get('miner_mode', False) else 'Disabled'}")
        
    def show_chain(self, *args) -> None:
        """Show the full blockchain."""
        response = self._make_request('chain')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        chain = response.get('chain', [])
        length = response.get('length', 0)
        
        print(f"\nBlockchain Length: {length}")
        print("--------------------")
        
        for i, block in enumerate(chain):
            print(f"Block #{block['index']}")
            print(f"  Hash: {block['hash'][:16]}...")
            print(f"  Previous Hash: {block['previous_hash'][:16]}...")
            print(f"  Timestamp: {time.ctime(block['timestamp'])}")
            print(f"  Transactions: {len(block['transactions'])}")
            print(f"  Nonce: {block['nonce']}")
            print()
            
    def validate_chain(self, *args) -> None:
        """Validate the blockchain."""
        response = self._make_request('chain/validate')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        valid = response.get('valid', False)
        length = response.get('length', 0)
        
        if valid:
            print(f"\n✅ Blockchain is valid (length: {length})")
        else:
            print(f"\n❌ Blockchain is NOT valid (length: {length})")
            
    def show_balance(self, *args) -> None:
        """Show balance for an address."""
        if not args or not args[0]:
            print("Error: Address required")
            print("Usage: balance <address>")
            return
            
        address = args[0]
        response = self._make_request(f'balance/{address}')
        
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        print(f"\nBalance for {address}: {response.get('balance', 0)}")
        
    def create_transaction(self, *args) -> None:
        """Create a new transaction."""
        if len(args) < 3:
            print("Error: Sender, recipient, and amount required")
            print("Usage: transaction <from> <to> <amount>")
            return
            
        sender = args[0]
        recipient = args[1]
        
        try:
            amount = float(args[2])
        except ValueError:
            print("Error: Amount must be a number")
            return
            
        # Create transaction
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }
        
        response = self._make_request('transactions/new', method='POST', data=transaction)
        
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        print(f"\nTransaction created: {response.get('message', '')}")
        
    def show_pending_transactions(self, *args) -> None:
        """Show pending transactions."""
        response = self._make_request('transactions/pending')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        transactions = response.get('transactions', [])
        count = response.get('count', 0)
        
        print(f"\nPending Transactions: {count}")
        print("----------------------")
        
        for i, tx in enumerate(transactions):
            print(f"Transaction #{i+1}")
            print(f"  From: {tx['sender']}")
            print(f"  To: {tx['recipient']}")
            print(f"  Amount: {tx['amount']}")
            print(f"  Timestamp: {time.ctime(tx['timestamp'])}")
            print()
            
    def show_rejected_transactions(self, *args) -> None:
        """Show rejected transactions."""
        response = self._make_request('transactions/rejected')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        transactions = response.get('transactions', [])
        count = response.get('count', 0)
        
        print(f"\nRejected Transactions: {count}")
        print("-----------------------")
        
        for i, item in enumerate(transactions):
            tx = item['transaction']
            reason = item['reason']
            
            print(f"Transaction #{i+1}")
            print(f"  From: {tx['sender']}")
            print(f"  To: {tx['recipient']}")
            print(f"  Amount: {tx['amount']}")
            print(f"  Reason: {reason}")
            print()
            
    def mine_block(self, *args) -> None:
        """Mine a new block."""
        response = self._make_request('mine')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        if 'message' in response:
            print(f"\n{response['message']}")
            
        if 'block' in response:
            block = response['block']
            print(f"Block #{block['index']} mined")
            print(f"  Hash: {block['hash'][:16]}...")
            print(f"  Transactions: {len(block['transactions'])}")
            
    def start_mining(self, *args) -> None:
        """Start continuous mining."""
        response = self._make_request('mine/start')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        print(f"\n{response.get('message', 'Mining started')}")
        
    def stop_mining(self, *args) -> None:
        """Stop continuous mining."""
        response = self._make_request('mine/stop')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        print(f"\n{response.get('message', 'Mining stopped')}")
        
    def show_peers(self, *args) -> None:
        """Show registered nodes and their active status."""
        response = self._make_request('nodes/peers')
        if 'error' in response:
            print(f"Error: {response['error']}")
            print("\nPossible causes:")
            print("- The node server might not be running")
            print("- There might be connectivity issues")
            print("\nTry running 'info' to check node status.")
            return
        
        nodes = response.get('nodes', [])
        active_count = response.get('active_count', 0)
        total_count = response.get('total_count', 0)
        
        print(f"\nRegistered Nodes: {total_count} (Active: {active_count})")
        print("-----------------------------------------")
        
        if total_count == 0:
            print("No registered nodes found in configuration.")
            print("To add a node, use: register <node_url>")
            print("Example: register http://localhost:5001")
            return
        
        # Display active nodes first
        print("\nACTIVE NODES:")
        print("------------")
        active_found = False
        
        for i, node in enumerate(nodes):
            if node.get('active', False):
                active_found = True
                name = node.get('name', 'Unnamed Node')
                url = node.get('url', 'Unknown URL')
                print(f"{i+1}. {name} - {url}")
                
        if not active_found:
            print("No active nodes found.")
            
        # Display inactive nodes
        print("\nINACTIVE NODES:")
        print("-------------")
        inactive_found = False
        
        for i, node in enumerate(nodes):
            if not node.get('active', False):
                inactive_found = True
                name = node.get('name', 'Unnamed Node')
                url = node.get('url', 'Unknown URL')
                print(f"{i+1}. {name} - {url}")
                
        if not inactive_found:
            print("No inactive nodes found.")
            
        print("\nCommands:")
        print("  - 'register <url>' to add a new node")
        print("  - 'consensus' to sync the blockchain with active nodes")
            
    def register_node(self, *args) -> None:
        """Register a new peer node."""
        if not args or not args[0]:
            print("Error: Node URL required")
            print("Usage: register <url>")
            return
            
        node_url = args[0]
        response = self._make_request('nodes/register', method='POST', data={'nodes': [node_url]})
        
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        print(f"\n{response.get('message', '')}")
        
    def run_consensus(self, *args) -> None:
        """Run the consensus algorithm."""
        response = self._make_request('nodes/resolve')
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        print(f"\n{response.get('message', '')}")
        
    def show_block(self, *args) -> None:
        """Show details for a specific block."""
        if not args or not args[0]:
            print("Error: Block index required")
            print("Usage: block <index>")
            return
            
        try:
            index = int(args[0])
        except ValueError:
            print("Error: Index must be a number")
            return
            
        response = self._make_request(f'blocks/{index}')
        
        if 'error' in response or 'message' in response and response.get('message') == 'Block not found':
            print(f"Error: Block not found")
            return
            
        print(f"\nBlock #{response['index']}")
        print("-------------")
        print(f"Hash: {response['hash']}")
        print(f"Previous Hash: {response['previous_hash']}")
        print(f"Timestamp: {time.ctime(response['timestamp'])}")
        print(f"Nonce: {response['nonce']}")
        print(f"Difficulty: {response['difficulty']}")
        print(f"Transactions: {len(response['transactions'])}")
        
        if response['transactions']:
            print("\nTransactions:")
            for i, tx in enumerate(response['transactions']):
                print(f"  {i+1}. From: {tx['sender']} To: {tx['recipient']} Amount: {tx['amount']}")
                
    def show_transaction_history(self, *args) -> None:
        """Show transaction history for an address."""
        if not args or not args[0]:
            print("Error: Address required")
            print("Usage: history <address>")
            return
            
        address = args[0]
        response = self._make_request(f'transactions/address/{address}')
        
        if 'error' in response:
            print(f"Error: {response['error']}")
            return
            
        transactions = response.get('transactions', [])
        count = response.get('count', 0)
        
        print(f"\nTransaction History for {address}: {count} transactions")
        print("--------------------------------------------------")
        
        for i, item in enumerate(transactions):
            tx = item['transaction']
            block_index = item['block_index']
            
            # Determine if this address is sender or recipient
            is_sender = tx['sender'] == address
            
            if is_sender:
                print(f"{i+1}. SENT {tx['amount']} to {tx['recipient']} (Block #{block_index})")
            else:
                print(f"{i+1}. RECEIVED {tx['amount']} from {tx['sender']} (Block #{block_index})")
                
    def exit_cli(self, *args) -> None:
        """Exit the CLI."""
        print("\nExiting blockchain CLI...")
        sys.exit(0)
        
    def process_command(self, command_line: str) -> None:
        """
        Process a command from the command line.
        
        Args:
            command_line: The command line string to process
        """
        parts = command_line.strip().split()
        if not parts:
            return
            
        command = parts[0].lower()
        args = parts[1:]
        
        if command in self.commands:
            # Handle nested commands like 'mining start'
            if isinstance(self.commands[command], dict) and args and args[0] in self.commands[command]:
                self.commands[command][args[0]](*args[1:])
            elif callable(self.commands[command]):
                self.commands[command](*args)
            else:
                print(f"Unknown subcommand: {command} {args[0] if args else ''}")
        else:
            print(f"Unknown command: {command}")
            
    def run_interactive(self) -> None:
        """Run the CLI in interactive mode."""
        print("\nBlockchain CLI")
        print("--------------")
        print("Type 'help' for available commands")
        print("Type 'exit' to quit")
        
        while True:
            try:
                command_line = input("\n> ")
                self.process_command(command_line)
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    def run_command(self, command_line: str) -> None:
        """
        Run a single command and exit.
        
        Args:
            command_line: The command line string to process
        """
        try:
            self.process_command(command_line)
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Blockchain Network CLI")
    parser.add_argument('--node', default='http://localhost:5000', help='Node address (default: http://localhost:5000)')
    parser.add_argument('command', nargs='*', help='Command to run (if not specified, runs in interactive mode)')
    
    args = parser.parse_args()
    cli = BlockchainCLI(args.node)
    
    if args.command:
        command_line = ' '.join(args.command)
        cli.run_command(command_line)
    else:
        cli.run_interactive()
        
        
if __name__ == '__main__':
    main()
