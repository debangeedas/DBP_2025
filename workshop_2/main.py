#!/usr/bin/env python3

import argparse
import logging
import sys
import threading
import time
from typing import Optional

from blockchain import Blockchain
from node import Node
from api import BlockchainAPI
from cli import BlockchainCLI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Distributed Blockchain Application')
    
    # Node configuration
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the node on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the node on')
    parser.add_argument('--difficulty', type=int, default=4, help='Mining difficulty (number of leading zeros required)')
    
    # Node type
    parser.add_argument('--node-type', choices=['full', 'miner'], default='full',
                        help='Type of node to run (full or miner)')
    parser.add_argument('--mining-interval', type=int, default=30, 
                        help='Mining interval in seconds (for miner nodes)')
    
    # Network configuration
    parser.add_argument('--peers', nargs='*', help='List of peer nodes to connect to')
    
    # UI options
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode instead of API server')
    parser.add_argument('--api', action='store_true', help='Run API server (default if no UI option is specified)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Default to API if no UI option specified
    if not args.cli and not args.api:
        args.api = True
        
    return args

def start_api_server(node: Node, host: str, port: int, debug: bool = False) -> None:
    """Start the API server."""
    api = BlockchainAPI(node)
    api.start(host, port, debug)

def start_cli(node_address: str) -> None:
    """Start the CLI interface."""
    cli = BlockchainCLI(node_address)
    cli.run_interactive()

def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Create the blockchain
        blockchain = Blockchain(difficulty=args.difficulty)
        
        # Create the node
        is_miner = args.node_type == 'miner'
        # Use a longer status cache time to reduce frequent API calls
        node = Node(
            host=args.host,
            port=args.port,
            blockchain=blockchain,
            miner_mode=is_miner,
            mining_interval=args.mining_interval,
            status_cache_time=60  # Cache node status for 60 seconds
        )
        
        # Connect to peers if specified
        if args.peers:
            for peer in args.peers:
                success = node.register_with_node(peer)
                if success:
                    logger.info(f"Connected to peer: {peer}")
                else:
                    logger.warning(f"Failed to connect to peer: {peer}")
        
        # Announce this node to all registered peers
        logger.info("Announcing this node to the network...")
        node.announce_to_peers()
        
        # Start mining if in miner mode
        if is_miner:
            logger.info(f"Starting miner node with mining interval of {args.mining_interval} seconds")
            node.start_mining()
        else:
            logger.info("Starting full node (non-mining mode)")
            
        # Run the appropriate interface
        if args.api:
            logger.info(f"Starting API server on {args.host}:{args.port}")
            start_api_server(node, args.host, args.port, args.debug)
        elif args.cli:
            # The CLI needs to connect to an API server
            node_address = f"http://{args.host}:{args.port}"
            
            # Start API in a separate thread
            api_thread = threading.Thread(
                target=start_api_server,
                args=(node, args.host, args.port, args.debug)
            )
            api_thread.daemon = True
            api_thread.start()
            
            # Give API time to start
            time.sleep(1)
            
            # Start CLI
            logger.info(f"Starting CLI connected to {node_address}")
            start_cli(node_address)
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
