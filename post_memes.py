import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import dotenv_values

from collection.reddit import fetch_reddit
from insta.instagrapi import InstaAdapter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = ROOT_DIR / "output"
ASSETS_DIR = ROOT_DIR / "assets"
POSTED_IDS_FILE = ROOT_DIR / "posted_ids.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("topmemes")

# ---------------------------------------------------------------------------
# Config constants
# ---------------------------------------------------------------------------
MEMES_SUBS = [
    "r/funny",
    # "r/memes",
    # "r/AdviceAnimals",
    # "r/dankmemes",
]

SOCCER_SUBS = [
    "r/soccercirclejerk",
]

HASH_TAGS = ""


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------
def load_posted_ids() -> set:
    """Load the set of Reddit post IDs that have already been posted."""
    if POSTED_IDS_FILE.exists():
        try:
            with open(POSTED_IDS_FILE, "r") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            logger.warning("Could not read %s — starting fresh", POSTED_IDS_FILE)
    return set()


def save_posted_ids(ids: set) -> None:
    """Persist the set of posted IDs to disk."""
    with open(POSTED_IDS_FILE, "w") as f:
        json.dump(sorted(ids), f, indent=2)


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def _sub_to_filename(subreddit: str) -> str:
    """Convert 'r/funny' → 'r_funny'."""
    return subreddit.replace("/", "_", 1)


def _output_path(subreddit: str) -> Path:
    return OUTPUT_DIR / f"{_sub_to_filename(subreddit)}.json"


def is_modified_today(file_path: Path) -> bool:
    today = datetime.now().date()
    try:
        filetime = datetime.fromtimestamp(file_path.stat().st_mtime)
    except (FileNotFoundError, OSError):
        return False
    return filetime.date() == today


def save(subreddit: str, data: list) -> None:
    """Save fetched data to a JSON file in the output directory."""
    path = _output_path(subreddit)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w") as outfile:
            json.dump(data, outfile, indent=2)
        logger.info("Saved %d posts to %s", len(data), path.name)
    except Exception as e:
        logger.error("Error saving data for %s: %s", subreddit, e)
        raise


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------
def save_from_list(r_list: list, limit: int | None = None) -> None:
    """Fetch and save posts for each subreddit that hasn't been updated today."""
    for subreddit in r_list:
        path = _output_path(subreddit)
        if not is_modified_today(path):
            data = fetch_reddit(subreddit, limit=limit)
            save(subreddit, data)
        else:
            logger.info("Skipping %s — already fetched today", subreddit)


def download_assets(subreddit: str) -> None:
    """Download image/video assets for posts not yet uploaded."""
    path = _output_path(subreddit)
    with open(path, "r") as f:
        posts = json.load(f)

    logger.info("Downloading assets from %s", subreddit)
    for post in posts:
        # Skip NSFW content
        if post.get("over_18"):
            logger.info("Skipping NSFW post: %s", post.get("title", "")[:60])
            continue

        if post.get("post_hint") == "image" and "posted_on" not in post:
            try:
                response = requests.get(post["url"], timeout=30)
                response.raise_for_status()
                image_name = post["url"].split("/")[-1]
                filepath = ASSETS_DIR / image_name
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "wb") as image_file:
                    image_file.write(response.content)
                post["file_name"] = image_name
                logger.info("Downloaded: %s", image_name)
            except requests.RequestException as e:
                logger.error("Failed to download image %s: %s", post.get("url"), e)

    with open(path, "w") as f:
        json.dump(posts, f, indent=2)


def upload_from(
    adapter: InstaAdapter,
    subreddit: str,
    posted_ids: set,
    dry_run: bool = False,
) -> None:
    """Upload posts to Instagram, skipping NSFW and already-posted content."""
    path = _output_path(subreddit)
    with open(path, "r") as f:
        posts = json.load(f)

    logger.info("Uploading to Instagram from %s", subreddit)

    for post in posts:
        post_id = post.get("id")

        # Skip already-posted (by JSON flag or by posted_ids set)
        if "posted_on" in post or post_id in posted_ids:
            continue

        # Skip NSFW content
        if post.get("over_18"):
            logger.info("Skipping NSFW post: %s", post.get("title", "")[:60])
            continue

        if post.get("post_hint") not in ("image", "hosted:video"):
            continue

        if dry_run:
            caption = (post.get("title") or "") + HASH_TAGS
            logger.info("[DRY RUN] Would upload: %s", caption[:60])
            continue

        if adapter.upload_post(post, ASSETS_DIR, HASH_TAGS):
            if post_id:
                posted_ids.add(post_id)

    # Save updated JSON
    with open(path, "w") as f:
        json.dump(posts, f, indent=2)


# ---------------------------------------------------------------------------
# Asset cleanup
# ---------------------------------------------------------------------------
def cleanup_assets(subreddit: str) -> None:
    """Delete local asset files for posts that have already been uploaded."""
    path = _output_path(subreddit)
    if not path.exists():
        return

    with open(path, "r") as f:
        posts = json.load(f)

    removed = 0
    for post in posts:
        if "posted_on" not in post:
            continue
        file_name = post.get("file_name")
        if not file_name:
            continue
        asset_path = ASSETS_DIR / file_name
        if asset_path.exists():
            asset_path.unlink()
            removed += 1
        # Also clean up video thumbnails / converted files
        for suffix in (".mp4", ".mp4.jpg"):
            extra = ASSETS_DIR / (post.get("id", "") + suffix)
            if extra.exists():
                extra.unlink()
                removed += 1

    if removed:
        logger.info("Cleaned up %d asset files for %s", removed, subreddit)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download top Reddit memes and upload them to Instagram.",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="memes",
        choices=["memes", "soccer", "football"],
        help="Which account/subreddit group to target (default: memes)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download assets but skip Instagram uploads",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Override the number of posts to fetch per subreddit",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete local assets for already-uploaded posts",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Use browser (Selenium) for upload instead of the API",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = dotenv_values(".env")
    if not config:
        logger.error("No .env file found")
        sys.exit(1)

    required_keys = ["USERNAME", "PASSWORD", "SOCCER_ACCOUNT_USERNAME", "SOCCER_ACCOUNT_PASSWORD"]
    missing = [k for k in required_keys if not config.get(k)]
    if missing:
        logger.error("Missing required .env keys: %s", ", ".join(missing))
        sys.exit(1)

    # Select account & subreddits based on mode
    is_soccer = args.mode in ("soccer", "football")
    if is_soccer:
        user_subs = SOCCER_SUBS
        username = config["SOCCER_ACCOUNT_USERNAME"]
        password = config["SOCCER_ACCOUNT_PASSWORD"]
        session_id = config.get("SOCCER_SESSION_ID")
        totp_secret = config.get("SOCCER_TOTP_SECRET")
    else:
        user_subs = MEMES_SUBS
        username = config["USERNAME"]
        password = config["PASSWORD"]
        session_id = config.get("SESSION_ID")
        totp_secret = config.get("TOTP_SECRET")

    # Ensure output & assets directories exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)

    # Fetch & save
    logger.info("Fetching posts for: %s", ", ".join(user_subs))
    save_from_list(user_subs, limit=args.limit)

    # Download assets
    for sub in user_subs:
        download_assets(sub)

    # Upload (unless dry-run)
    posted_ids = load_posted_ids()

    if not args.dry_run:
        if args.browser:
            from insta.browser import BrowserAdapter

            adapter = BrowserAdapter(username, password, assets_dir=ASSETS_DIR)
            try:
                logger.info("Logging in as %s (browser mode)", username)
                adapter.login(session_id=session_id)
            except Exception as e:
                logger.error("Browser login failed: %s", e)
                adapter.close()
                sys.exit(1)
        else:
            adapter = InstaAdapter(username, password, session_dir=ROOT_DIR)
            proxy = config.get("PROXY")
            if proxy:
                adapter.set_proxy(proxy)
            try:
                logger.info("Logging in as %s", username)
                adapter.login(session_id=session_id, totp_secret=totp_secret)
            except Exception:
                sys.exit(1)

        for sub in user_subs:
            upload_from(adapter, sub, posted_ids)

        save_posted_ids(posted_ids)

        # Close browser if used
        if args.browser:
            adapter.close()
    else:
        logger.info("[DRY RUN] Skipping Instagram login and uploads")
        for sub in user_subs:
            upload_from(None, sub, posted_ids, dry_run=True)

    # Cleanup if requested
    if args.cleanup:
        for sub in user_subs:
            cleanup_assets(sub)

    logger.info("Done.")


if __name__ == "__main__":
    main()
