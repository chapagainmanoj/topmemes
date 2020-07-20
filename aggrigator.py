import os
import json
import requests
from collection.reddit import fetch_reddit
from instamate.upload_mate import upload_post
# from instamate.upload import upload_post


def save(subreddit, data):
    try:
        file_name = subreddit.replace('/', '_', 1)
        with open ('output/{}.json'.format(file_name), 'w+') as outfile:
            json.dump(sub_data, outfile, indent=2)
    except Exception as e:
        print("Unexpected error", e)
        raise

def save_from_list(r_list):
    for sub in r_list:
        data = fetch_reddit(subreddit);
        save(sub, data)

def upload_from(subreddit):
    print('Downloading assets from {}'.format(subreddit))
    file_name = subreddit.replace('/', '_', 1)
    with open("output/{}.json".format(file_name)) as f:
        posts = json.load(f)
    try:
        for post in posts:
            if post['post_hint'] == "image":
                image = requests.get(post["url"])
                if image.status_code == 200:
                    image_name = post["url"].split('/')[-1]
                    with open("assets/{}".format(image_name), 'wb') as image_file:
                        image_file.write(image.content)
                        upload_post("assets/{}".format(image_name), post["title"])
    except Exception as e:
        print("Unexpected error", e)
        raise

if __name__ == "__main__":
    # save_from_list(['r/AdviceAnimals', 'r/memes', 'r/MemeEconomy', 'r/dankmemes'])
    for sub in ['r/AdviceAnimals', 'r/memes', 'r/MemeEconomy', 'r/dankmemes']:
        upload_from(sub)
