from instapy_cli import client
from .settings import USERNAME, PASSWORD

def upload_post(image, description):
    with client(USERNAME, PASSWORD) as cli:
        cli.upload(image, description)
