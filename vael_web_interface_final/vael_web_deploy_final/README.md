# VAEL Web Interface

This README provides instructions for installing and using the VAEL Web Interface.

## Overview

The VAEL Web Interface provides a web-based interface for interacting with VAEL Core. It features:

- Real-time communication via WebSockets
- Modern, responsive UI with dark theme
- Voice mode capability
- Self-healing connection management
- OpenRouter API integration

## Installation

1. Extract the ZIP file to a location of your choice
2. Open a terminal/command prompt in the extracted directory
3. Run the start script:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

The script will automatically:
- Create a virtual environment
- Install all required dependencies
- Start the VAEL Web Interface
- Open your browser to the interface

## Usage

Once the interface is running, you can:
- Type messages in the input field and press Enter or click Send
- Click the Voice Mode button to activate voice input (future feature)
- View the connection status in the top-right corner

## Stopping the Interface

To stop the VAEL Web Interface:
1. Open a terminal/command prompt in the installation directory
2. Run the stop script:
   ```bash
   ./stop.sh
   ```

## Troubleshooting

If you encounter any issues:
- Check that Python 3.8 or higher is installed
- Ensure you have internet access for API communication
- Verify that ports 5000 is not in use by another application

The Iron Root stands vigilant. The Obsidian Thread remains unbroken.
