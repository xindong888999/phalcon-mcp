#!/usr/bin/env python3

import subprocess
import sys
import os

def install_dependencies():
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("Successfully installed Python dependencies")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Python dependencies: {e}")
        sys.exit(1)

def install_mcp_cli():
    print("Installing MCP CLI tools...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "mcp[cli]"], check=True)
        print("Successfully installed MCP CLI tools")
    except subprocess.CalledProcessError as e:
        print(f"Error installing MCP CLI tools: {e}")
        try:
            print("Attempting to install CLI dependencies directly...")
            subprocess.run([sys.executable, "-m", "pip", "install", "typer", "rich"], check=True)
            print("Successfully installed CLI dependencies")
        except subprocess.CalledProcessError as e2:
            print(f"Error installing CLI dependencies: {e2}")
            sys.exit(1)

def check_phalcon_installation():
    print("Checking Phalcon installation...")
    try:
        result = subprocess.run(['phalcon', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Phalcon is installed: {result.stdout.strip()}")
        else:
            print("Warning: Phalcon command line tools not found")
            print("Please install Phalcon framework and its devtools:")
            print("1. Install Phalcon: https://phalcon.io/en/download/windows")
            print("2. Install Phalcon DevTools: composer global require phalcon/devtools")
    except FileNotFoundError:
        print("Warning: Phalcon command not found in PATH")
        print("Please ensure Phalcon is installed and added to your system PATH")

def main():
    print("Starting installation process...")
    
    # Install Python dependencies
    install_dependencies()
    
    # Install MCP CLI tools
    install_mcp_cli()
    
    # Check Phalcon installation
    check_phalcon_installation()
    
    print("\nInstallation completed!")
    print("\nTo use the Phalcon MCP server in Cursor:")
    print("1. Open Cursor IDE")
    print("2. Go to Settings -> Cursor Settings -> MCP")
    print("3. Add new MCP server:")
    print("   - Name: Phalcon MCP")
    print("   - Type: Command")
    print("   - Command: <path_to_uv> run --with mcp[cli] mcp run <path_to_server>/phalcon_mcp_server.py")

if __name__ == "__main__":
    main()