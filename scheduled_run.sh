#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/topmemes.log"

# Activate virtualenv
if [ -d "${SCRIPT_DIR}/.venv" ]; then
    source "${SCRIPT_DIR}/.venv/bin/activate"
else
    echo "$(date): Virtual environment not found at ${SCRIPT_DIR}/.venv" | tee -a "$LOG_FILE"
    exit 1
fi

# Function to check internet connection
check_internet() {
    ping -c 1 -W 5 8.8.8.8 &> /dev/null
}

# Check internet connection
if check_internet; then
    echo "$(date): Internet connection detected. Running post_memes.py..." | tee -a "$LOG_FILE"
    python "${SCRIPT_DIR}/post_memes.py" --cleanup "$@" >> "$LOG_FILE" 2>&1
else
    echo "$(date): No internet connection detected." | tee -a "$LOG_FILE"
fi