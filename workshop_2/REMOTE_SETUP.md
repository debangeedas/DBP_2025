# Remote Server Setup Guide for Blockchain Network

This guide will help you set up the blockchain application on an external server (like Cato) so that multiple students can interact with the network from different locations.

## Initial Server Setup

### Step 1: Access Your Server

1. Connect to your server via SSH:
   ```
   ssh your_username@your_server_ip
   ```

2. Navigate to the directory where you want to install the blockchain application:
   ```
   cd /path/to/directory
   ```

### Step 2: Transfer the Codebase to Your Server

You have several options to transfer the blockchain application code to your server:

#### Option 1: Using Git (Recommended)

If Git is installed on your server:

```bash
# Clone the repository directly on your server
git clone https://github.com/your-repository/blockchain-app.git
cd blockchain-app
```

#### Option 2: Using SCP (Secure Copy)

From your local machine, use SCP to transfer the files:

```bash
# Run this command from your LOCAL computer
scp -r /path/to/local/blockchain-app your_username@your_server_ip:/path/on/server/
```

Example:
```bash
scp -r ~/workshop_2 student@cato-server.edu:~/blockchain
```

#### Option 3: Using SFTP

1. Connect to your server with SFTP:
   ```bash
   sftp your_username@your_server_ip
   ```

2. Navigate to the destination directory:
   ```bash
   cd /path/on/server/
   ```

3. Create a directory for the blockchain application:
   ```bash
   mkdir blockchain-app
   cd blockchain-app
   ```

4. Upload the files:
   ```bash
   put -r /path/to/local/blockchain-app/*
   ```

#### Option 4: Using a ZIP Archive

1. On your local machine, create a ZIP archive:
   ```bash
   zip -r blockchain-app.zip /path/to/blockchain-app/
   ```

2. Transfer the ZIP file to your server:
   ```bash
   scp blockchain-app.zip your_username@your_server_ip:/path/on/server/
   ```

3. On the server, unzip the archive:
   ```bash
   cd /path/on/server/
   unzip blockchain-app.zip
   ```

### Step 3: Install Dependencies

After transferring the code to your server, install the required dependencies:

```bash
cd /path/to/blockchain-app
pip install -r requirements.txt
```

## Running Nodes on External Servers

### Important: Using External IP Addresses

When running the blockchain on external servers, you must:

1. Use the server's actual IP address or hostname, not `localhost` or `127.0.0.1`
2. Configure the firewall to allow traffic on the ports you're using
3. Use `0.0.0.0` as the host to allow external connections to your node
4. Specify your server's public IP with `--external-ip` for proper node identification

### Step 1: Start the First Node (Server A)

Run the first node on your server with:

```bash
python main.py --host 0.0.0.0 --port 5000 --node-type full --difficulty 4 --external-ip SERVER_A_PUBLIC_IP
```

This makes your node accessible from the internet at `http://SERVER_A_PUBLIC_IP:5000`

### Step 2: Start the Second Node (Server B)

On your second server, connect to the first node by specifying it as a peer:

```bash
python main.py --host 0.0.0.0 --port 5000 --node-type full --difficulty 4 --external-ip SERVER_B_PUBLIC_IP --peers http://SERVER_A_PUBLIC_IP:5000
```

### Troubleshooting Peer Connections

If nodes are not connecting properly, verify:

1. **Firewall settings**: Ensure ports 5000 is open on both servers

   ```bash
   # On Ubuntu/Debian
   sudo ufw allow 5000/tcp
   
   # On CentOS/RHEL
   sudo firewall-cmd --permanent --add-port=5000/tcp
   sudo firewall-cmd --reload
   ```

2. **Correct IP usage**: 
   - Always use the server's public IP address for the `--external-ip` parameter
   - Use full URLs with `http://` prefix for the `--peers` parameter
   - Never use localhost, 127.0.0.1, or 0.0.0.0 in the peers list

3. **Network Connectivity**: Test basic connectivity between servers

   ```bash
   # From Server A, test connection to Server B
   ping SERVER_B_PUBLIC_IP
   curl http://SERVER_B_PUBLIC_IP:5000/chain
   ```

4. **Check Configuration File**: After starting nodes, verify the peers are correctly saved

   ```bash
   cat nodes_config.json
   ```
   
   The file should contain entries with the correct public IPs, not local addresses.

### Step 3: Start a Miner Node

On the same server or a different one, start a miner node:

```
python main.py --host 0.0.0.0 --port 5001 --node-type miner --peer http://FIRST_SERVER_IP:5000 --mining-interval 30
```

Replace `FIRST_SERVER_IP` with the actual IP address of the server running your first node.

## Connecting Multiple Students

### Student Connection Instructions

Provide these instructions to students who will connect to your blockchain network:

1. Clone or download the blockchain application code

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Connect to the existing network (replace SERVER_IP with your actual server IP):
   ```
   python main.py --host 127.0.0.1 --port 5000 --node-type full --peer http://SERVER_IP:5000 --cli
   ```

4. They can now interact with the blockchain network through the CLI

## Network Configuration Tips

### Firewall Settings

Make sure your server's firewall allows incoming and outgoing TCP connections on the ports you're using:

```
sudo ufw allow 5000/tcp
sudo ufw allow 5001/tcp
```

### Security Considerations

- This application is for educational purposes and doesn't implement authentication
- Consider running it on a private network if possible
- Use a VPN if students need to access it from outside the campus network

### Testing Connectivity

Students can verify they're connected to the network by using these commands in the CLI:

```
peers          # Should show the other nodes in the network
chain          # Should show the current blockchain
```

## Troubleshooting

### Cannot Connect to Remote Node

If students can't connect to your node:

1. Verify the IP address and port are correct
2. Check if the server firewall is allowing connections
3. Ensure the node is running with `--host 0.0.0.0` to accept external connections

### Transactions Not Appearing

If transactions created on one node don't appear on others:

1. Check if the nodes are properly connected (use `peers` command)
2. Verify that all nodes have the correct network configuration
3. Restart the nodes if necessary

## Advanced: Setting Up a Stable Network

For a more stable setup where the network persists even when students disconnect:

1. Run at least one full node and one miner node on permanent servers
2. Use a process manager like `supervisor` or `systemd` to keep the nodes running
3. Create a simple script for students to connect to your permanent nodes
