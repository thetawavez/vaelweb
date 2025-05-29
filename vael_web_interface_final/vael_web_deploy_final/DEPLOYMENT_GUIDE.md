# VAEL Web Interface - Deployment Guide

This guide provides instructions for deploying the VAEL Web Interface, a web-based interface for interacting with VAEL Core.

## Overview

The VAEL Web Interface provides:
- Real-time communication via WebSockets
- Modern, responsive UI with dark theme
- Voice mode capability (future feature)
- Self-healing connection management
- OpenRouter API integration

## Deployment Options

### Option 1: Local Deployment (Recommended for Most Users)

1. Extract the ZIP file to a location of your choice
2. Open a terminal/command prompt in the extracted directory
3. Make the deployment script executable:
   ```bash
   chmod +x deploy.sh
   ```
4. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

The script will automatically:
- Check for Python installation
- Create a virtual environment
- Install all required dependencies
- Start the VAEL Web Interface
- Open your browser to the interface

### Option 2: Manual Deployment

If you prefer to deploy manually or the automated script doesn't work for your environment:

1. Extract the ZIP file to a location of your choice
2. Open a terminal/command prompt in the extracted directory
3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Create logs directory:
   ```bash
   mkdir -p logs/async_pipeline
   ```
7. Start the application:
   ```bash
   cd src
   python -m main
   ```
8. Open your browser and navigate to: `http://localhost:5000`

### Option 3: Web Hosting Deployment

For deployment on web hosting platforms:

1. Upload the entire package to your hosting provider
2. Ensure your hosting provider supports Python 3.8+ and Flask applications
3. Configure your hosting provider to:
   - Create a virtual environment
   - Install dependencies from requirements.txt
   - Set the entry point to src/main.py
   - Set the Flask application variable to `app`

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
- Verify that port 5000 is not in use by another application
- Check the logs directory for error messages

The Iron Root stands vigilant. The Obsidian Thread remains unbroken.
