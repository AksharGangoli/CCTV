#!/bin/bash
# ============================================================
# CCTV SMART MONITOR - EASY SETUP SCRIPT
# ============================================================
# Just run this file and everything will be installed!
# Usage: bash setup.sh
# ============================================================

echo "=========================================="
echo "  CCTV Smart Monitor - Setup"
echo "=========================================="
echo ""

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${YELLOW}[1/6] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}  Found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}  Python3 not found! Please install Python 3.8+${NC}"
    echo "  Download from: https://www.python.org/downloads/"
    exit 1
fi

# Check pip
echo -e "${YELLOW}[2/6] Checking pip...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}  Found: pip3${NC}"
else
    echo -e "${RED}  pip3 not found! Installing...${NC}"
    python3 -m ensurepip --upgrade
fi

# Create virtual environment
echo -e "${YELLOW}[3/6] Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
echo -e "${GREEN}  Virtual environment created!${NC}"

# Install system dependencies (for face_recognition)
echo -e "${YELLOW}[4/6] Installing system dependencies...${NC}"
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update -qq
    sudo apt-get install -y -qq cmake build-essential libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
elif command -v yum &> /dev/null; then
    # CentOS/Fedora
    sudo yum install -y cmake gcc-c++ openblas-devel lapack-devel libX11-devel gtk3-devel
elif command -v brew &> /dev/null; then
    # macOS
    brew install cmake
fi
echo -e "${GREEN}  System dependencies installed!${NC}"

# Install Python packages
echo -e "${YELLOW}[5/6] Installing Python packages (this may take a few minutes)...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}  All packages installed!${NC}"

# Create necessary directories
echo -e "${YELLOW}[6/6] Setting up directories...${NC}"
mkdir -p storage/faces
mkdir -p storage/plates
mkdir -p recordings
mkdir -p logs
mkdir -p reports
mkdir -p known_faces
mkdir -p demo_videos
echo -e "${GREEN}  Directories created!${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}  SETUP COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "  NEXT STEPS:"
echo "  1. Edit config.yaml to add your cameras"
echo "  2. Add known faces to 'known_faces/' folder"
echo "     (name the files like: person_name.jpg)"
echo "  3. Run the system:"
echo "     python3 main.py"
echo ""
echo "  For demo mode (no cameras needed):"
echo "     python3 main.py --demo"
echo ""
echo "  Web Dashboard will be at:"
echo "     http://localhost:5000"
echo ""
echo "  For help:"
echo "     python3 main.py --help"
echo ""
echo "=========================================="
