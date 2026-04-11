#!/bin/bash
echo "=== Environment Check ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version 2>&1 || echo 'Python3 not found')"
echo "Pip version: $(pip3 --version 2>&1 || echo 'Pip3 not found')"
echo "Listing files:"
ls -la
echo "=== End Check ==="