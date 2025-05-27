import click
import requests
import json
from typing import Optional

SERVER_URL = 'http://131.226.220.69:5000'

class AliasedGroup(click.Group):
    def format_commands(self, ctx, formatter):
        # Group commands by callback
        rows = []
        seen = set()
        for cmd_name, cmd in self.commands.items():
            if cmd.callback is None:
                continue
            # Find all names for this callback (short and long)
            if id(cmd.callback) in seen:
                continue
            aliases = [name for name, c in self.commands.items() if c.callback == cmd.callback]
            seen.add(id(cmd.callback))
            # Show all aliases comma-separated, description from the first
            rows.append((", ".join(aliases), cmd.get_short_help_str()))
        if rows:
            with formatter.section('Commands'):
                formatter.write_dl(rows)

# CLI command aliases mapping:
# create-user      -> cu
# add-transaction  -> at
# show-chain       -> sc
# show-block       -> sb
# show-balances    -> bal
# show-invalid     -> si
# show-pending     -> sp
# reset            -> r
# export           -> ex

class BlockchainCLI:
    def __init__(self, server_url=SERVER_URL):
        self.server_url = server_url

    def add_transaction(self, source: str, recipient: str, amount: float) -> bool:
        """Add a new transaction to the blockchain"""
        try:
            print(f"Attempting transaction: {source} -> {recipient} for ${amount:.2f}")
            response = requests.post(
                f"{self.server_url}/transactions/new",
                json={
                    'source': source,
                    'recipient': recipient,
                    'amount': amount
                }
            )
            
            if response.status_code == 201:
                print(f"✓ SUCCESS: Transaction added successfully")
                return True
            else:
                try:
                    # Try to parse as JSON for detailed error
                    error_data = response.json()
                    error_msg = f"✗ FAILED: {error_data.get('error', 'Unknown error')}"
                    
                    if 'reason' in error_data:
                        error_msg += f"\n   Reason: {error_data['reason']}"
                        
                        # Add helpful hints based on error type
                        if "user 'alice' does not exist" in error_data['reason']:
                            error_msg += f"\n   Hint: Create user 'alice' with 'create-user alice'"
                        elif "user 'Charlie' does not exist" in error_data['reason']:
                            error_msg += f"\n   Hint: Create user 'Charlie' with 'create-user Charlie'"
                        elif "does not exist" in error_data['reason']:
                            # Extract username from error message
                            import re
                            match = re.search(r"'([^']+)' does not exist", error_data['reason'])
                            if match:
                                username = match.group(1)
                                error_msg += f"\n   Hint: Create user '{username}' with 'create-user {username}'"
                    
                    print(error_msg)
                except ValueError:
                    # Fallback for non-JSON responses
                    print(f"✗ FAILED: {response.text}")
                    
                return False
                
        except requests.exceptions.ConnectionError:
            print("✗ ERROR: Could not connect to the server. Make sure it's running.")
            return False
        except Exception as e:
            print(f"✗ ERROR: An unexpected error occurred: {str(e)}")
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

    def export_blockchain(self, filepath: str) -> bool:
        """Export complete blockchain data to a JSON file"""
        try:
            print(f"Exporting blockchain data to {filepath}...")
            response = requests.post(
                f"{self.server_url}/export",
                json={'filepath': filepath}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ SUCCESS: {data.get('message', 'Export successful')}")
                print(f"Exported to: {data.get('filepath', filepath)}")
                return True
            else:
                try:
                    error_data = response.json()
                    print(f"✗ FAILED: {error_data.get('error', 'Unknown error')}")
                except ValueError:
                    print(f"✗ FAILED: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("✗ ERROR: Could not connect to the server. Make sure it's running.")
            return False
        except Exception as e:
            print(f"✗ ERROR: An unexpected error occurred: {str(e)}")
            return False
        
    def create_user(self, username: str) -> bool:
        """Create a new user with a starting balance"""
        try:
            response = requests.post(
                f"{self.server_url}/users/create",
                json={'username': username}
            )
            if response.status_code == 201:
                print(f"User '{username}' created successfully with starting balance of $100.00")
                return True
            else:
                print(f"Failed to create user: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running.")
            return False

@click.group(cls=AliasedGroup)
@click.option('--server', default=SERVER_URL, help='Server URL')
@click.pass_context
def cli(ctx, server):
    """Blockchain CLI Tool"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = BlockchainCLI(server)

@cli.command('add-transaction')
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

cli.add_command(add_transaction, 'at')

@cli.command('show-chain')
@click.pass_context
def show_chain(ctx):
    """Show the entire blockchain"""
    chain = ctx.obj['cli'].print_chain()
    if chain:
        print(json.dumps(chain, indent=2))

cli.add_command(show_chain, 'sc')

@cli.command('show-block')
@click.argument('index', type=int)
@click.pass_context
def show_block(ctx, index):
    """Show a specific block"""
    block = ctx.obj['cli'].print_block(index)
    if block:
        print(json.dumps(block, indent=2))

cli.add_command(show_block, 'sb')

@cli.command('show-balances')
@click.pass_context
def show_balances(ctx):
    """Show all account balances"""
    balances = ctx.obj['cli'].print_balances()
    if balances:
        print("\n" + "=" * 40)
        print("💰 USER BALANCES")
        print("=" * 40)
        
        if not balances:
            print("No users found. Create users with 'create-user' command.")
        else:
            # Find the longest username for formatting
            max_len = max([len(name) for name in balances.keys()]) if balances else 0
            
            # Sort by username
            for account in sorted(balances.keys()):
                balance = balances[account]
                # Add color indicators based on balance
                if balance > 0:
                    indicator = "🟢"  # green circle
                else:
                    indicator = "🔴"  # red circle
                    
                print(f"{indicator} {account.ljust(max_len + 2)}${balance:.2f}")
                
        print("=" * 40)

cli.add_command(show_balances, 'bal')


@cli.command('show-invalid')
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
        
    print("\n" + "=" * 60)
    print(f"🚫 INVALID TRANSACTIONS: {len(invalid['invalid_transactions'])}")
    print("=" * 60)
    
    for i, tx in enumerate(invalid['invalid_transactions'], 1):
        print(f"\n{i}. Transaction Details:")
        print(f"   Source:      {tx['source']}")
        print(f"   Recipient:   {tx['recipient']}")
        print(f"   Amount:      ${float(tx['amount']):.2f}")
        if 'timestamp' in tx:
            from datetime import datetime
            timestamp = datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"   Timestamp:   {timestamp}")
        print(f"   Error:       {tx.get('validation_error', 'Unknown error')}")
        print(f"   " + "-" * 56)
    
    print("\n" + "=" * 60)

cli.add_command(show_invalid, 'si')

@cli.command('reset')
@click.pass_context
def reset(ctx):
    """Reset the blockchain"""
    if click.confirm('Are you sure you want to reset the blockchain? This will delete all blocks, transactions, and user balances.'):
        print("\nResetting blockchain...")
        if ctx.obj['cli'].reset_blockchain():
            print("✓ SUCCESS: Blockchain has been reset to genesis state")
            print("All blocks, transactions, and user balances have been cleared.")
            print("You will need to create new users again with the 'create-user' command.")
        else:
            print("✗ ERROR: Failed to reset blockchain")

cli.add_command(reset, 'r')

@cli.command('export')
@click.argument('filepath')
@click.pass_context
def export(ctx, filepath):
    """Export blockchain data to a JSON file"""
    ctx.obj['cli'].export_blockchain(filepath)

cli.add_command(export, 'ex')

@cli.command('create-user')
@click.argument('username')
@click.pass_context
def create_user(ctx, username):
    """Create a new user with starting balance"""
    print(f"Creating new user '{username}'...")
    if ctx.obj['cli'].create_user(username):
        print("✓ User created with starting balance of $100.00")
    else:
        print("✗ Failed to create user - user may already exist or server error occurred")

cli.add_command(create_user, 'cu')

@cli.command('show-pending')
@click.pass_context
def show_pending(ctx):
    """Show all valid transactions waiting to be added to a block"""
    response = requests.get(f"{ctx.obj['cli'].server_url}/pending")
    if response.status_code == 200:
        transactions = response.json()
        
        print("\n" + "=" * 60)
        print("⏳ PENDING TRANSACTIONS")
        print("=" * 60)
        
        if not transactions:
            print("No pending transactions found")
        else:
            print(f"Found {len(transactions)} transaction{'s' if len(transactions) != 1 else ''} waiting to be added to a block\n")
            
            for i, tx in enumerate(transactions, 1):
                print(f"{i}. Transaction Details:")
                print(f"   Source:      {tx['source']}")
                print(f"   Recipient:   {tx['recipient']}")
                print(f"   Amount:      ${float(tx['amount']):.2f}")
                if 'timestamp' in tx:
                    from datetime import datetime
                    timestamp = datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"   Timestamp:   {timestamp}")
                print(f"   " + "-" * 56)
        
        print("\nThese transactions will be added to a new block when there are 3 transactions.")
        print("=" * 60)
    else:
        print("✗ Error fetching pending transactions")
        print(f"Server response: {response.text}")
        print("Make sure the blockchain server is running.")

cli.add_command(show_pending, 'sp')

if __name__ == '__main__':
    cli(obj={})
