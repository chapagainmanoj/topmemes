import os
import json
import requests
from collection.reddit import fetch_reddit
from instamate.upload import upload_post
# from instamate.upload import upload_post


def save(subreddit, data):
    try:
        file_name = subreddit.replace('/', '_', 1)
        with open ('output/{}.json'.format(file_name), 'w+') as outfile:
            json.dump(data, outfile, indent=2)
    except Exception as e:
        print("Unexpected error", e)
        raise

def save_from_list(r_list):
    for subreddit in r_list:
        data = fetch_reddit(subreddit);
        save(subreddit, data)

def download_assets(subreddit):
    file_name = subreddit.replace('/', '_', 1)
    with open("output/{}.json".format(file_name), 'r') as f:
        posts = json.load(f)
        print(posts, 'before')
    try:
        print('Downloading assets from {}'.format(subreddit))
        for post in posts:
            if post['post_hint'] == "image" and not 'posted_on' in post:
                image = requests.get(post["url"])
                if image.status_code == 200:
                    image_name = post["url"].split('/')[-1]
                    with open("assets/{}".format(image_name), 'wb') as image_file:
                        image_file.write(image.content)
                        # upload_post("assets/{}".format(image_name), post["title"])
                        meta = {}
                        meta["file_name"] = image_name
                        post.update(meta)
        with open("output/{}.json".format(file_name), 'w') as f:
            json.dump(posts, f, indent=2)
    except Exception as e:
        print("Unexpected error", e)
        raise

def upload_from(subreddit):
    file_name = subreddit.replace('/', '_', 1)
    with open("output/{}.json".format(file_name), 'r') as f:
        posts = json.load(f)
    try:
        print('Uploading to insta from {}'.format(subreddit))
        new_posts = upload_post(posts)
        with open("output/{}.json".format(file_name), 'w') as f:
            json.dump(new_posts, f, indent=2)
    except Exception as e:
        raise

if __name__ == "__main__":
    # save_from_list(['r/dankmemes'])
    # download_assets('r/dankmemes')
    upload_from('r/dankmemes')
    # save_from_list(['r/AdviceAnimals', 'r/memes', 'r/MemeEconomy', 'r/dankmemes'])
    # for sub in ['r/AdviceAnimals', 'r/memes', 'r/MemeEconomy', 'r/dankmemes']:
    #     upload_from(sub)
