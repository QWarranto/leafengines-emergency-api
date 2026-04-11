#!/bin/bash
echo "=== Starting setup ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la

echo "=== Installing dependencies ==="
python -m pip install --upgrade pip
python -m pip install Flask gunicorn

echo "=== Verifying installation ==="
python -c "import flask; print(f'Flask version: {flask.__version__}')"
python -c "import gunicorn; print('Gunicorn available')"
which gunicorn || echo "gunicorn not in PATH"
python -m gunicorn --version

echo "=== Setup complete ==="