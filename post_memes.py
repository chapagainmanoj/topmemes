import os
import sys
import json
import requests
from collection.reddit import fetch_reddit
from instagrapi import Client
from dotenv import dotenv_values
from moviepy.editor import VideoFileClip
from datetime import datetime
from pathlib import Path
import yt_dlp

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBS = [
    "r/funny",  #
    # "r/memes",
    # "r/AdviceAnimals",
    # "r/dankmemes",
]
# HASH_TAGS = "\n \n #memes_orgy #meme #memes #funny #dankmemes #memesdaily #funnymemes #lol #follow #dank #humor #like #love #dankmeme #tiktok #lmao #instagram #comedy #ol #anime #fun #dailymemes #memepage #edgymemes #offensivememes #memestagram #funnymeme"
HASH_TAGS = ""


def convert_gif_to_mp4(gif_path: Path) -> Path:
    mp4_path = gif_path.with_suffix(".mp4")
    try:
        clip = VideoFileClip(str(gif_path))
        clip.write_videofile(str(mp4_path), codec="libx264")
        return mp4_path
    except Exception as e:
        print(f"Error converting GIF to MP4: {e}")
        return None


def is_modified_today(file_name: str) -> bool:
    today = datetime.now().date()
    try:
        filetime = datetime.fromtimestamp(os.path.getmtime(file_name))
    except Exception as e:
        print(f"Error checking file modification date: {e}")
        return False
    return filetime.date() == today


def save(subreddit: str, data: dict) -> None:
    try:
        file_name = subreddit.replace("/", "_", 1)
        fullpath = f"{ROOT_DIR}/output/{file_name}.json"
        path = Path(fullpath)
        path.touch(exist_ok=True)
        with open(path, "w+") as outfile:
            json.dump(data, outfile, indent=2)
    except Exception as e:
        print(f"Unexpected error while saving data: {e}")
        raise


def save_from_list(r_list: list) -> None:
    for subreddit in r_list:
        file_name = subreddit.replace("/", "_", 1)
        file = f"{ROOT_DIR}/output/{file_name}.json"
        if not is_modified_today(file):
            data = fetch_reddit(subreddit)
            save(subreddit, data)


def download_assets(subreddit: str) -> None:
    file_name = subreddit.replace("/", "_", 1)
    with open(f"{ROOT_DIR}/output/{file_name}.json", "r") as f:
        posts = json.load(f)
    try:
        print(f"Downloading assets from {subreddit}")
        for post in posts:
            if post.get("post_hint") == "image" and "posted_on" not in post:
                image = requests.get(post["url"])
                if image.status_code == 200:
                    image_name = post["url"].split("/")[-1]
                    filepath = Path(f"{ROOT_DIR}/assets/{image_name}")
                    with open(filepath, "wb") as image_file:
                        image_file.write(image.content)
                        meta = {"file_name": image_name}
                        post.update(meta)
        with open(f"{ROOT_DIR}/output/{file_name}.json", "w") as f:
            json.dump(posts, f, indent=2)
    except Exception as e:
        print(f"Unexpected error while downloading assets: {e}")
        raise


def download_video(url: str, output_path: Path) -> bool:
    ydl_opts = {
        "outtmpl": str(output_path),
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False


def upload_from(instaBot: Client, subreddit: str) -> None:
    file_name = subreddit.replace("/", "_", 1)
    with open(f"{ROOT_DIR}/output/{file_name}.json", "r") as f:
        posts = json.load(f)
        print(f"Uploading to insta from {subreddit}")
    for post in posts:
        if (
            post.get("post_hint") in ["image", "hosted:video"]
            and "posted_on" not in post
            # and "error" not in post
        ):
            caption = post.get("title") + HASH_TAGS
            image_name = post.get("file_name")
            image_path = Path(f"{ROOT_DIR}/assets/{image_name}")
            ext = image_path.suffix.lower()
            print("Uploading post:", caption, image_path)
            try:
                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    instaBot.photo_upload(image_path, caption)
                    post["posted_on"] = datetime.now().isoformat()
                elif ext in [".gifv", ".gif"]:
                    mp4_path = convert_gif_to_mp4(image_path)
                    if mp4_path:
                        instaBot.clip_upload(mp4_path, caption)
                        post["posted_on"] = datetime.now().isoformat()
                    else:
                        post["error"] = "Failed to convert GIF to MP4"
                elif post.get("is_video") and post.get("post_hint") == "hosted:video":
                    video_url = post["media"]["reddit_video"]["dash_url"]
                    video_name = post["id"] + ".mp4"
                    video_path = Path(f"{ROOT_DIR}/assets/{video_name}")
                    if download_video(video_url, video_path):
                        instaBot.clip_upload(video_path, caption)
                        post["posted_on"] = datetime.now().isoformat()
                    else:
                        post["error"] = "Failed to download video"
                else:
                    print(f"Unsupported file format: {post['url']}")
            except Exception as e:
                post["error"] = str(e)
                print(f"Error uploading post: {e}")

    with open(f"{ROOT_DIR}/output/{file_name}.json", "w") as f:
        json.dump(posts, f, indent=2)


if __name__ == "__main__":
    user_subs = sys.argv[1:]

    if not user_subs:
        user_subs = SUBS

    save_from_list(user_subs)

    instaBot = Client()
    config = dotenv_values(".env")
    instaBot.login(username=config["USERNAME"], password=config["PASSWORD"])

    for current_sub in user_subs:
        download_assets(current_sub)
        upload_from(instaBot, current_sub)
