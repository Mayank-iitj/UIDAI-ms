#!/bin/bash
# UIDAI Intelligence System - Run Script
# Linux/Mac Shell Script for Easy Execution

echo "============================================================"
echo "   UIDAI INTELLIGENCE SYSTEM"
echo "   Production Deployment Runner"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Please install Python 3.9 or higher."
    exit 1
fi

# Navigate to script directory
cd "$(dirname "$0")"

echo "[INFO] Current directory: $(pwd)"
echo "[INFO] Starting UIDAI Intelligence System..."
echo ""

# Run the main system
python3 main.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Analysis completed successfully!"
    echo ""
    echo "Reports saved to: outputs/reports/"
    echo ""
else
    echo ""
    echo "[ERROR] System encountered an error. Check outputs/system.log for details."
    exit 1
fi
