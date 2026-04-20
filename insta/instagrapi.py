"""Instagram adapter — handles login, session management, and uploads."""

import logging
import time
from pathlib import Path

from instagrapi import Client

logger = logging.getLogger(__name__)

# Seconds to wait between Instagram uploads (rate-limit)
UPLOAD_DELAY = 5


class InstaAdapter:
    """Wraps instagrapi.Client with session persistence and multi-strategy login."""

    def __init__(self, username: str, password: str, session_dir: Path):
        self.username = username
        self.password = password
        self.session_file = session_dir / f"session_{username}.json"
        self.client = Client()

    def set_proxy(self, proxy: str) -> None:
        self.client.set_proxy(proxy)
        logger.info("Using proxy: %s", proxy.split("@")[-1] if "@" in proxy else proxy)

    def login(
        self,
        session_id: str | None = None,
        totp_secret: str | None = None,
    ) -> None:
        """Attempt login using multiple strategies in priority order."""
        try:
            # Strategy 1: Load saved session
            if self.session_file.exists():
                logger.info("Loading saved session from %s", self.session_file.name)
                self.client.load_settings(self.session_file)
                self.client.login(self.username, self.password)
                logger.info("Session restored successfully")

            # Strategy 2: TOTP-based 2FA login
            elif totp_secret:
                import pyotp

                totp = pyotp.TOTP(totp_secret)
                verification_code = totp.now()
                logger.info("Logging in with TOTP verification code")
                self.client.login(
                    self.username, self.password, verification_code=verification_code
                )

            # Strategy 3: Session ID login
            elif session_id:
                self.client.login_by_sessionid(session_id)

            # Strategy 4: Plain password login
            else:
                self.client.login(self.username, self.password)

            # Save session for future runs
            self.client.dump_settings(self.session_file)
            logger.info("Session saved to %s", self.session_file.name)

        except Exception as e:
            error_msg = str(e)
            if "blacklist" in error_msg.lower() or "BadPassword" in type(e).__name__:
                logger.error(
                    "Instagram login failed — your IP may be blacklisted.\n"
                    "  Solutions:\n"
                    '  1. Set TOTP_SECRET in .env for 2FA login\n'
                    '  2. Set PROXY in .env (e.g. PROXY = "http://user:pass@host:port")\n'
                    "  3. Try from a different network (VPN, mobile hotspot)\n"
                    "  4. Wait a few hours and retry\n"
                    "  Original error: %s",
                    e,
                )
            else:
                logger.error("Instagram login failed: %s", e)

            # Delete stale session file
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("Deleted stale session file")
            raise

    def upload_photo(self, path: Path, caption: str) -> None:
        self.client.photo_upload(path, caption)

    def upload_clip(self, path: Path, caption: str) -> None:
        self.client.clip_upload(path, caption)

    def upload_post(self, post: dict, assets_dir: Path, hash_tags: str = "") -> bool:
        """Upload a single post (image, GIF, or video) to Instagram.

        Returns True if uploaded successfully, False otherwise.
        Updates post dict in-place with posted_on or error.
        """
        from datetime import datetime

        caption = (post.get("title") or "") + hash_tags
        file_name = post.get("file_name")

        if not file_name:
            logger.warning("No file_name for post %s — skipping", post.get("id"))
            return False

        asset_path = assets_dir / file_name
        ext = asset_path.suffix.lower()

        logger.info("Uploading: %s", caption[:80])
        try:
            if ext in (".jpg", ".jpeg", ".png", ".webp"):
                self.upload_photo(asset_path, caption)
            elif ext in (".gifv", ".gif"):
                mp4_path = self._convert_gif_to_mp4(asset_path)
                if mp4_path:
                    self.upload_clip(mp4_path, caption)
                else:
                    post["error"] = "Failed to convert GIF to MP4"
                    return False
            elif post.get("is_video") and post.get("post_hint") == "hosted:video":
                video_url = post["media"]["reddit_video"]["dash_url"]
                video_name = post["id"] + ".mp4"
                video_path = assets_dir / video_name
                if self._download_video(video_url, video_path):
                    self.upload_clip(video_path, caption)
                else:
                    post["error"] = "Failed to download video"
                    return False
            else:
                logger.warning("Unsupported format: %s", post.get("url"))
                return False

            post["posted_on"] = datetime.now().isoformat()
            logger.info("✓ Uploaded: %s", post.get("title", "")[:60])
            time.sleep(UPLOAD_DELAY)
            return True

        except Exception as e:
            post["error"] = str(e)
            logger.error("Error uploading post: %s", e)
            return False

    @staticmethod
    def _convert_gif_to_mp4(gif_path: Path) -> Path | None:
        mp4_path = gif_path.with_suffix(".mp4")
        try:
            from moviepy.editor import VideoFileClip

            clip = VideoFileClip(str(gif_path))
            clip.write_videofile(str(mp4_path), codec="libx264", logger=None)
            clip.close()
            logger.info("Converted GIF → MP4: %s", mp4_path.name)
            return mp4_path
        except Exception as e:
            logger.error("Error converting GIF to MP4: %s", e)
            return None

    @staticmethod
    def _download_video(url: str, output_path: Path) -> bool:
        import yt_dlp

        ydl_opts = {
            "outtmpl": str(output_path),
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info("Downloaded video: %s", output_path.name)
            return True
        except Exception as e:
            logger.error("Error downloading video: %s", e)
            return False
