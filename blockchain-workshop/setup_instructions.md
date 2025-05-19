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
   ```bash
   python -m cli.cli --help
   ```

## Troubleshooting

- If you get a "port already in use" error, you can change the port in `server/server.py` by modifying the `run_server()` function call at the bottom of the file.
- Make sure to activate the virtual environment before running any commands.
- If you encounter any module not found errors, make sure to install the requirements using `pip install -r requirements.txt`.
