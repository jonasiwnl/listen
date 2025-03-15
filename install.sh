#!/bin/bash

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null
then
    echo "ffmpeg could not be found. Installing ffmpeg..."
    if ! command -v brew &> /dev/null
    then
        echo "Homebrew is not installed. Please install Homebrew first."
        exit 1
    fi
    brew install ffmpeg
else
    echo "ffmpeg is already installed."
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install Python3 first."
    exit 1
fi

# Create a virtual environment
python3 -m venv listen-venv
source listen-venv/bin/activate

# Install required Python packages
pip install openai-whisper

# Make the listen.py script executable
chmod +x listen.py

# Create a symbolic link to the listen.py script
ln -sf "$(pwd)/listen.py" /usr/local/bin/listen

echo "Installation complete. You can now run the tool using the command 'listen'."
