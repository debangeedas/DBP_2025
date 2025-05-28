# Blockchain Peer Connection Guide

This guide provides troubleshooting steps and best practices for ensuring proper connections between blockchain nodes.

## Running Different Node Types

### Step 1: Start Your First Node

Let's start with a full node:

```
python main.py --host 0.0.0.0 --port 5000 --node-type full --cli
```

This starts a full node on your computer with a command-line interface so you can interact with it.

### Step 2: Start a Mining Node

Open a new command prompt or terminal window and run:

```
python main.py --host 0.0.0.0 --port 5001 --node-type miner --cli
```

This starts a mining computer that connects to your first node and can create new blocks.

## Troubleshooting Connection Issues

If nodes are not connecting properly, verify:

1. **Firewall settings**: Ensure ports 5000 is open on both servers

2. **Check Configuration File**: After starting nodes, verify the peers are correctly saved

   ```bash
   cat nodes_config.json
   ```
   
   The file should contain entries with the correct public IPs, not local addresses.

## Managing the nodes_config.json File

### Understanding nodes_config.json

The `nodes_config.json` file is a critical component that stores information about all nodes in your blockchain network. When nodes register with each other, they save peer information in this file.

### Viewing the Configuration

To check what nodes are currently registered in your network:

```bash
cat nodes_config.json
```

A healthy configuration should look like this:

```json
{
  "nodes": [
    {
      "host": "131.226.220.72",
      "port": 5000,
      "url": "http://131.226.220.72:5000"
    },
    {
      "host": "131.226.220.73",
      "port": 5000,
      "url": "http://131.226.220.73:5000"
    }
  ]
}
```

### Manual Editing

If you need to manually edit the configuration file:

1. Stop all running nodes
2. Edit the file with your preferred text editor:
   ```bash
   nano nodes_config.json
   ```
3. Make necessary changes (ensure valid JSON format)
4. Save and restart your nodes

### Resetting the Configuration

If your configuration becomes corrupted or you want to start fresh:

```bash
rm nodes_config.json
```

A new file will be created automatically when you start a node again.

