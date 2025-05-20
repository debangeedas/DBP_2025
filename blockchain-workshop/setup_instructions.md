# Blockchain Workshop Setup Instructions

## Prerequisites

### Windows
1. Download and install Python 3.8 or later from [python.org](https://www.python.org/downloads/windows/)
   - During installation, make sure to check "Add Python to PATH"
2. Open Command Prompt and verify the installation:
   ```
   python --version
   pip --version
   ```

### Mac
1. Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python:
   ```bash
   brew install python
   ```
3. Verify the installation:
   ```bash
   python3 --version
   pip3 --version
   ```

## Setup Instructions

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/debangeedas/DBP_2025.git
   cd DBP_2025\blockchain-workshop
   ```

2. Create a virtual environment:
   - Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
## Running the Application

1. Run the server:
   ```bash
   python -m server.server
   ```

2. In a new terminal window (with the virtual environment activated), use the CLI (detailed instructions are given in the file cli_guide.md):
   - **Windows (PowerShell):**
     ```bash
     .\bcli --help
     ```
     (If using Command Prompt, you can use `bcli --help`)

   - **Mac/Linux:**
     ```bash
     python -m cli.cli --help
     ```

   > **Tip:** On Windows, use the `bcli` command for all CLI operations. This batch script is located in the project root and wraps the full Python command for you. On Mac/Linux, you can optionally create an alias like `alias bcli='python -m cli.cli'` in your shell profile for convenience.

   You can now use `bcli` commands in your terminal. Each command has a short and long form:

| Short Form      | Long Form            | Example (Short)      | Example (Long)                |
|:---------------:|:--------------------|:---------------------|:------------------------------|
| cu              | create-user         | bcli cu alice        | bcli create-user alice        |
| at              | add-transaction     | bcli at alice bob 10 | bcli add-transaction alice bob 10 |
| sc              | show-chain          | bcli sc              | bcli show-chain               |
| sb              | show-block          | bcli sb 1            | bcli show-block 1             |
| bal             | show-balances       | bcli bal             | bcli show-balances            |
| si              | show-invalid        | bcli si              | bcli show-invalid             |
| sp              | show-pending        | bcli sp              | bcli show-pending             |
| r               | reset               | bcli r               | bcli reset                    |
| ex              | export              | bcli ex              | bcli export                   |

**Tip:**
- Use the short form for speed and convenience (interactive use).
- Use the long form for clarity (scripts, docs, teaching).

## How it works

- The blockchain automatically creates a new block after every 3 transactions
- Users must be explicitly created using the `create-user` command, each starting with $100.00
- Transactions between non-existent users will be rejected and logged as invalid
- All blockchain data can be exported to a JSON file using the `export` command
- All data is stored in memory and will be lost when the server is stopped
- The genesis block is created automatically when the blockchain is initialized

## Troubleshooting

- If you get a "port already in use" error, you can change the port in `server/server.py` by modifying the `run_server()` function call at the bottom of the file.
- Make sure to activate the virtual environment before running any commands.
- If you encounter any module not found errors, make sure to install the requirements using `pip install -r requirements.txt`.
