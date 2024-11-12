#!/bin/bash

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Migrate database
flask db upgrade

# Run Flask application
flask --app=app:app --debug run --host=0.0.0.0 --port=5001
