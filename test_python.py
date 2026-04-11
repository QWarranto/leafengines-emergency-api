#!/usr/bin/env python3
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError:
    print("Flask not installed")

try:
    import gunicorn
    print("Gunicorn available")
except ImportError:
    print("Gunicorn not installed")