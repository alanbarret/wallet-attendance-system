#!/bin/bash

echo "================================================"
echo "🔐 Phantom Wallet Attendance System"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup.sh"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

# Check if required packages are installed
python -c "import flask, cryptography, qrcode, pyngrok" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Required packages not found!"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup.sh"
    echo ""
    exit 1
fi

echo "✓ All dependencies found"
echo ""

# Run the application
echo "🚀 Starting Phantom Wallet Attendance System..."
echo ""
python app.py
