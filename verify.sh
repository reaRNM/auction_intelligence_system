#!/bin/bash

echo "Verifying Auction Intelligence System Setup"
echo "=========================================="

# Check directory structure
echo -e "\nChecking directory structure:"
tree -L 3 ~/auction_intelligence_system

# Check virtual environment
echo -e "\nChecking virtual environment:"
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
    source venv/bin/activate
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
else
    echo "✗ Virtual environment not found"
fi

# Check permissions
echo -e "\nChecking permissions:"
echo "Project root: $(ls -ld ~/auction_intelligence_system)"
echo "Data directories: $(ls -ld ~/auction_intelligence_system/data/*)"

# Check Python path
echo -e "\nChecking Python path:"
which python

# Check configuration files
echo -e "\nChecking configuration files:"
ls -l ~/auction_intelligence_system/config/

# Check core modules
echo -e "\nChecking core modules:"
ls -l ~/auction_intelligence_system/app/core/

# Check web interface
echo -e "\nChecking web interface:"
ls -l ~/auction_intelligence_system/app/web/

# Check CLI tools
echo -e "\nChecking CLI tools:"
ls -l ~/auction_intelligence_system/app/cli/

# Check documentation
echo -e "\nChecking documentation:"
ls -l ~/auction_intelligence_system/docs/

# Check test suite
echo -e "\nChecking test suite:"
ls -l ~/auction_intelligence_system/tests/

echo -e "\nVerification complete!" 