#!/bin/bash

LOG_FILE="aggrigator.log"

# Function to check internet connection
check_internet() {
    ping -c 1 8.8.8.8 &> /dev/null
    if [ $? -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Check internet connection
if check_internet; then
    echo "$(date): Internet connection detected. Running post_memes.py..." | tee -a $LOG_FILE
    python post_memes.py >> $LOG_FILE 2>&1
else
    echo "$(date): No internet connection detected." | tee -a $LOG_FILE
fi