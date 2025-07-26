#!/bin/bash

# Test script for Bugcrowd MCP Server on macOS using uv
# This script helps test the MCP server functionality

echo "🔧 Bugcrowd MCP Server Test Script (uv)"
echo "======================================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed or not in PATH"
    echo "   Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "🔧 Creating uv virtual environment..."
    uv venv
fi

# Activate virtual environment and check dependencies
echo "📦 Activating virtual environment and checking dependencies..."
source .venv/bin/activate

# Install dependencies if not present
if ! uv pip list | grep -q "mcp\|httpx"; then
    echo "📦 Installing dependencies with uv..."
    uv add mcp httpx
fi

# Check if required environment variables are set
if [ -z "$BUGCROWD_API_USERNAME" ] || [ -z "$BUGCROWD_API_PASSWORD" ]; then
    echo "⚠️  Warning: BUGCROWD_API_USERNAME and BUGCROWD_API_PASSWORD environment variables are not set"
    echo "   Please set them before running the server:"
    echo "   export BUGCROWD_API_USERNAME='your_username'"
    echo "   export BUGCROWD_API_PASSWORD='your_password'"
    echo ""
fi

# Verify installation
if ! uv run python3 -c "import mcp, httpx; print('✅ Required packages (mcp, httpx) are available')" 2>/dev/null; then
    echo "❌ Dependencies not properly installed"
    exit 1
fi

# Navigate to project root (test script is in test/ subdirectory)
cd "$(dirname "$0")/.."

# Make the server script executable
chmod +x bugcrowd_mcp_server.py

echo ""
echo "🚀 Testing MCP Server Startup..."
echo "Press Ctrl+C to stop the server"
echo ""

# Test the server by running it with uv
uv run python3 bugcrowd_mcp_server.py