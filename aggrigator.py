import os
import sys
import json
import requests
import getopt
from collection.reddit import fetch_reddit
from instamate.upload import upload_post
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBS = ['r/AdviceAnimals', 'r/memes', 'r/MemeEconomy', 'r/dankmemes']

def isModifiedToday(file_name):
    today = datetime.now().date()
    try:
        filetime = datetime.fromtimestamp(os.path.getctime(file_name))
    except Exception as e:
        return False
    return filetime.date() == today

def save(subreddit, data):
    try:
        file_name = subreddit.replace('/', '_', 1)
        with open ('{}/output/{}.json'.format(ROOT_DIR, file_name), 'w+') as outfile:
            json.dump(data, outfile, indent=2)
    except Exception as e:
        print("Unexpected error", e)
        raise

def save_from_list(r_list):
    for subreddit in r_list:
        file_name = subreddit.replace('/', '_', 1)
        file = '{}/output/{}.json'.format(ROOT_DIR, file_name)
        if not isModifiedToday(file):
            data = fetch_reddit(subreddit);
            save(subreddit, data)

def download_assets(subreddit):
    file_name = subreddit.replace('/', '_', 1)
    with open("{}/output/{}.json".format(ROOT_DIR, file_name), 'r') as f:
        posts = json.load(f)
    try:
        print('Downloading assets from {}'.format(subreddit))
        for post in posts:
            if post['post_hint'] == "image" and not 'posted_on' in post:
                image = requests.get(post["url"])
                if image.status_code == 200:
                    image_name = post["url"].split('/')[-1]
                    with open("{}/assets/{}".format(ROOT_DIR, image_name), 'wb') as image_file:
                        image_file.write(image.content)
                        # upload_post("assets/{}".format(image_name), post["title"])
                        meta = {}
                        meta["file_name"] = image_name
                        post.update(meta)
        with open("{}/output/{}.json".format(ROOT_DIR, file_name), 'w') as f:
            json.dump(posts, f, indent=2)
    except Exception as e:
        print("Unexpected error", e)
        raise

def upload_from(subreddit):
    file_name = subreddit.replace('/', '_', 1)
    with open("{}/output/{}.json".format(ROOT_DIR, file_name), 'r') as f:
        posts = json.load(f)
    try:
        print('Uploading to insta from {}'.format(subreddit))
        new_posts = upload_post(posts)
        with open("{}/output/{}.json".format(ROOT_DIR, file_name), 'w') as f:
            json.dump(new_posts, f, indent=2)
    except Exception as e:
        raise


if __name__ == "__main__":
    user_subs = sys.argv[1:]

    if len(user_subs) < 1:
        user_subs = SUBS

    save_from_list(SUBS)

    ## download and save today's
    index = datetime.now().day % len(user_subs)
    current_sub = user_subs[index]

    download_assets(current_sub)
    upload_from(current_sub)
