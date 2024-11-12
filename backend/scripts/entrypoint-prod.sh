#!/bin/bash

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Migrate database
flask db upgrade

# Run application using Gunicorn
gunicorn -w 2 -b :5001 --log-level info --worker-class gevent --timeout 900 --keep-alive 750 app:app
