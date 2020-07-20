import requests

TOP = 'top'
NEW = 'new'
HOT = 'hot'
LIMIT = 5

def serialize(item):
    return { key: item["data"][key] for key in ("id", "title", "thumbnail", "url", "ups", "downs", "total_awards_received", "is_video", "post_hint") }

def fetch_reddit(subreddit = 'r/chelseafc', list_type = TOP, limit=5):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    headers = {'User-Agent': user_agent}
    url = "https://reddit.com/{}/{}.json?limit={}".format(subreddit, TOP, LIMIT)
    print("Fetching posts from {}".format(subreddit))
    response = requests.get(url, headers = headers)
    json_response = response.json()
    parsed_response = list(map(serialize, json_response["data"]["children"]))

    return parsed_response
