import logging
import time

import requests

logger = logging.getLogger(__name__)

TOP = "top"
NEW = "new"
HOT = "hot"
DEFAULT_LIMIT = 2
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}
SERIALIZE_KEYS = (
    "id",
    "title",
    "thumbnail",
    "url",
    "ups",
    "downs",
    "total_awards_received",
    "media",
    "secure_media",
    "is_video",
    "post_hint",
    "over_18",
)

# Per-subreddit fetch limit overrides
SUB_LIMITS = {
    "r/funny": 5,
}


def serialize(item):
    return {key: item["data"].get(key) for key in SERIALIZE_KEYS}


def fetch_reddit(subreddit="r/funny", list_type=TOP, limit=None):
    """Fetch top posts from a subreddit via Reddit's public JSON API."""
    if limit is None:
        limit = SUB_LIMITS.get(subreddit, DEFAULT_LIMIT)

    url = f"https://reddit.com/{subreddit}/{list_type}.json?limit={limit}"
    logger.info("Fetching %d posts from %s (%s)", limit, subreddit, list_type)

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        json_response = response.json()

        parsed_response = [serialize(child) for child in json_response["data"]["children"]]
        logger.info("Fetched %d posts from %s", len(parsed_response), subreddit)

        # Rate limit: pause briefly after each request
        time.sleep(2)
        return parsed_response
    except requests.RequestException as e:
        logger.error("Error fetching data from Reddit (%s): %s", subreddit, e)
        return []
