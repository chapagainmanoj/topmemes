import requests

TOP = "top"
NEW = "new"
HOT = "hot"
LIMIT = 5
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
    "is_video",
    "post_hint",
)


def serialize(item):
    return {key: item["data"].get(key) for key in SERIALIZE_KEYS}


def fetch_reddit(subreddit="r/chelseafc", list_type=TOP, limit=LIMIT):
    url = f"https://reddit.com/{subreddit}/{list_type}.json?limit={limit}"
    print(f"Fetching posts from {subreddit}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        json_response = response.json()
        parsed_response = list(map(serialize, json_response["data"]["children"]))
        return parsed_response
    except requests.RequestException as e:
        print(f"Error fetching data from Reddit: {e}")
        return []
