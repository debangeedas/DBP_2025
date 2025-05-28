# Remote Server Setup Guide for Blockchain Network

This guide will help you set up the blockchain application on an external server (like Cato) so that multiple students can interact with the network from different locations.

## Initial Server Setup

### Step 1: Access Your Server

1. Connect to your server via SSH:

```
ssh -i "path/to/key.pem" username@server_ip
```

Example:
   ```
   ssh -i "C:\Users\user\ecdsa-key-20250519.pem" cato-user@131.226.220.72
   ```

   Where to get your server IP: https://console.cato.digital/compute/server   

### Step 2: Setup your environment

The server should have Python 3 installed, however you would need to install Git and pip.

1. Install pip:
```bash
sudo yum install pip
```

2. Install Git (if not already installed):
```bash
sudo yum install git
```

### Step 3: Transfer the Codebase to Your Server

You have several options to transfer the blockchain application code to your server:

#### Option 1: Using Git (Recommended)

If you have Git installed on your server, you can clone the repository directly on your server:

```bash
# Clone the repository directly on your server
git clone https://github.com/debangeedas/DBP_2025.git
cd workshop_2
```

#### Option 2: Using SCP (Secure Copy)

From your local machine, use SCP to transfer the files:

```bash
# Run this command from your LOCAL computer
scp -i "path/to/your/key.pem" -r "path/to/local/blockchain-app" username@server_ip:/path/on/server/
```

Example:
```bash
scp -i "C:\Users\user\ecdsa-key-20250519.pem" -r "C:\Users\user\workshop_2" cato-user@131.226.220.72:/home/cato-user/workshop_2
```

### Step 4: Activate the virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### Step 5: Install Dependencies

After transferring the code to your server, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Step 6: Bypass the firewall

Run the following command on your local machine first to see behavior when the server is not accessible:
 
```bash
$ curl http://<IP>:5000
>> curl: (7) Failed to connect to <IP> port 5000 after 2113 ms: Connection refused
```
Run this on your remote server to bypass the firewall:

```bash
sudo firewall-cmd --zone public --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Step 7: Run the application

```bash
python main.py --host 0.0.0.0 --port 5000 --node-type miner --cli
```
Run this on your local machine to see behavior when the server is accessible:

```bash
$ curl http://<IP>:5001
>> {"message":"Resource not found"}
```

### Step 8: Run CLI commands

Watch the CLI output to see the node's behavior. Add transactions, check the chain, balances, etc.

1. Create transactions:
```bash
transaction Alice Bob 25
transaction Bob Charlie 10
transaction Alice Charlie 5
```

2. Watch as the mining node automatically creates a new block once it has 3 transactions!

3. Check balances/chain/pending transactions/invalid transactions/block details, etc.