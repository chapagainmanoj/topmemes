# topmemes

Automated Reddit → Instagram meme pipeline. Downloads top posts from configured subreddits and uploads them to Instagram accounts using the [instagrapi](https://github.com/subzeroid/instagrapi) API.

### Note for now only `--browser` is working:
- Try `python post_memes.py soccer --browser` with session id in `.env`




## Features

- Fetches top posts from multiple subreddits
- Downloads images and videos (via `yt-dlp`)
- Converts GIFs to MP4 for Instagram Reels
- NSFW content filtering
- Duplicate post detection (persistent across runs)
- Automatic asset cleanup after upload
- Dry-run mode for testing
- Structured logging

## Prerequisites

- **Python 3.10+**
- **ffmpeg** (required by `moviepy` for video processing)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## Installation

```bash
# Clone the repository
git clone https://github.com/chapagainmanoj/topmemes.git
cd topmemes

# Create and activate virtual environment
source venv.sh

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Instagram account credentials:

```env
USERNAME = "your_memes_account"
PASSWORD = "your_memes_password"

SOCCER_ACCOUNT_USERNAME = "your_soccer_account"
SOCCER_ACCOUNT_PASSWORD = "your_soccer_password"

# Optional: use session ID for login (avoids rate-limit issues)
# SESSION_ID = "your_session_id"
```

## Usage

```bash
# Post memes (default — uses r/funny)
python post_memes.py

# Post soccer memes
python post_memes.py soccer

# Download only — don't upload to Instagram
python post_memes.py --dry-run

# Fetch more posts per subreddit
python post_memes.py --limit 10

# Clean up uploaded assets after posting
python post_memes.py --cleanup

# Combine flags
python post_memes.py soccer --limit 5 --cleanup

# Show all options
python post_memes.py --help
```

## Scheduled Runs (Cron)

Use the included `scheduled_run.sh` which activates the virtualenv and checks for internet before running:

```bash
# Edit crontab
crontab -e

# Run every 6 hours
0 */6 * * * /path/to/topmemes/scheduled_run.sh

# Run daily at 9 AM (with soccer mode)
0 9 * * * /path/to/topmemes/scheduled_run.sh soccer
```

## Project Structure

```
topmemes/
├── post_memes.py          # Main entry point — download, upload, cleanup
├── collection/
│   ├── __init__.py
│   └── reddit.py          # Reddit API fetcher
├── assets/                # Downloaded images & videos (gitignored)
├── output/                # Cached post data per subreddit (gitignored)
├── posted_ids.json        # Persistent duplicate detection (gitignored)
├── scheduled_run.sh       # Cron wrapper script
├── venv.sh                # Virtual environment helper
├── requirements.txt       # Python dependencies
├── .env.example           # Credential template
└── README.md
```

## Instagram Accounts

- Memes: [memes_orgy](https://www.instagram.com/memes_orgy/)
- Soccer: [var.gone.mad](https://www.instagram.com/var.gone.mad/)