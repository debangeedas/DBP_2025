import click
import requests
import json
from typing import Optional, Dict, Any, List

class BlockchainCLI:
    def __init__(self, server_url='http://localhost:5000'):
        self.server_url = server_url

    def add_transaction(self, source: str, recipient: str, amount: float) -> bool:
        """Add a new transaction to the blockchain"""
        try:
            response = requests.post(
                f"{self.server_url}/transactions/new",
                json={
                    'source': source,
                    'recipient': recipient,
                    'amount': amount
                }
            )
            return response.status_code == 201
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running.")
            return False

    def print_chain(self) -> Optional[dict]:
        """Print the entire blockchain"""
        try:
            response = requests.get(f"{self.server_url}/chain")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running.")
            return None

    def print_block(self, index: int) -> Optional[dict]:
        """Print a specific block"""
        try:
            response = requests.get(f"{self.server_url}/block/{index}")
            if response.status_code == 200:
                return response.json()
            print(f"Error: {response.json().get('message', 'Unknown error')}")
            return None
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running.")
            return None

    def print_balances(self) -> Optional[dict]:
        """Print all balances"""
        try:
            response = requests.get(f"{self.server_url}/balances")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running.")
            return None

    def print_invalid_transactions(self) -> Optional[dict]:
        """Get all invalid transactions with their error messages"""
        try:
            response = requests.get(f"{self.server_url}/invalid")
            if response.status_code == 200:
                return response.json()
            print(f"Error: {response.text}")
            return None
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running.")
            return None

    def reset_blockchain(self) -> bool:
        """Reset the blockchain to its initial state"""
        try:
            response = requests.post(f"{self.server_url}/reset")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running.")
            return False

    def export_transactions(self, filepath: str) -> bool:
        """This method is kept for compatibility but does nothing"""
        print("Export functionality has been removed")
        return False

@click.group()
@click.option('--server', default='http://localhost:5000', help='Server URL')
@click.pass_context
def cli(ctx, server):
    """Blockchain CLI Tool"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = BlockchainCLI(server)

@cli.command()
@click.argument('source')
@click.argument('recipient')
@click.argument('amount', type=float)
@click.pass_context
def add_transaction(ctx, source, recipient, amount):
    """Add a new transaction"""
    if ctx.obj['cli'].add_transaction(source, recipient, amount):
        print("Transaction added successfully")
    else:
        print("Failed to add transaction")

@cli.command()
@click.pass_context
def show_chain(ctx):
    """Show the entire blockchain"""
    chain = ctx.obj['cli'].print_chain()
    if chain:
        print(json.dumps(chain, indent=2))

@cli.command()
@click.argument('index', type=int)
@click.pass_context
def show_block(ctx, index):
    """Show a specific block"""
    block = ctx.obj['cli'].print_block(index)
    if block:
        print(json.dumps(block, indent=2))

@cli.command()
@click.pass_context
def show_balances(ctx):
    """Show all account balances"""
    balances = ctx.obj['cli'].print_balances()
    if balances:
        for account, balance in balances.items():
            print(f"{account}: ${balance:.2f}")

@cli.command()
@click.pass_context
def show_invalid(ctx):
    """Show all invalid transactions with their error messages"""
    cli = ctx.obj['cli']
    invalid = cli.print_invalid_transactions()
    if invalid is None:
        return
        
    if not invalid.get('invalid_transactions'):
        print("No invalid transactions found")
        return
        
    print("\nInvalid Transactions:")
    for tx in invalid['invalid_transactions']:
        print(f"- {tx['source']} -> {tx['recipient']} (${tx['amount']}): {tx.get('validation_error', 'Unknown error')}")

@cli.command()
@click.pass_context
def reset(ctx):
    """Reset the blockchain"""
    if click.confirm('Are you sure you want to reset the blockchain? This will delete all blocks and start over.'):
        if ctx.obj['cli'].reset_blockchain():
            print("Blockchain reset successfully")
        else:
            print("Failed to reset blockchain")

@cli.command()
def export(ctx):
    """Export functionality has been removed"""
    print("Export functionality has been removed")

@cli.command()
@click.pass_context
def show_pending(ctx):
    """Show all valid transactions waiting to be added to a block"""
    response = requests.get(f"{ctx.obj['cli'].server_url}/pending")
    if response.status_code == 200:
        transactions = response.json()
        if not transactions:
            click.echo('No pending transactions')
            return
            
        click.echo('Pending Transactions:')
        click.echo('-' * 60)
        for tx in transactions:
            click.echo(f"From: {tx['source']} -> To: {tx['recipient']} | Amount: ${tx['amount']:.2f}")
        click.echo('-' * 60)
        click.echo(f'Total pending transactions: {len(transactions)}')
    else:
        click.echo('Error fetching pending transactions')
        click.echo(response.json().get('error', 'Unknown error'))

if __name__ == '__main__':
    cli(obj={})
