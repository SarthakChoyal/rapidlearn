#!/bin/bash

echo "Starting Rapid Learn..."
echo

# Change to the directory containing the script
cd "$(dirname "$0")"

# Check if venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Run the Flask application
echo "Starting Flask server..."
echo
echo "Please open your browser and go to: http://localhost:5000"
echo
python3 app.py

# Keep the terminal open if there's an error
if [ $? -ne 0 ]; then
    echo
    echo "An error occurred. Press any key to exit."
    read -n 1
fi 