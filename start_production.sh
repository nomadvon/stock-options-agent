#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install/update dependencies
pip install -r requirements.txt

# Start the production script
python run_production.py 