"""Browser-based Instagram adapter using Playwright (web upload, avoids mobile API blocks)."""

import logging
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class BrowserAdapter:
    """Upload to Instagram via browser automation (Playwright + Chromium)."""

    def __init__(self, username: str, password: str, assets_dir: Path):
        self.username = username
        self.password = password
        self.assets_dir = assets_dir
        self._playwright = None
        self._browser = None
        self.page = None

    def login(self, **kwargs) -> None:
        """Launch browser and login to Instagram.

        If session_id is provided, injects the cookie and skips the form login.
        """
        session_id = kwargs.get("session_id")

        self._playwright = sync_playwright().start()

        # Use iPhone emulation for mobile Instagram UI (has upload button)
        iphone = self._playwright.devices["iPhone 13"]

        self._browser = self._playwright.chromium.launch(headless=False)
        self.context = self._browser.new_context(**iphone)
        self.page = self.context.new_page()

        if session_id:
            # Inject session cookie and skip login form
            logger.info("Logging in with session ID (cookie injection)")
            self.context.add_cookies([
                {
                    "name": "sessionid",
                    "value": session_id,
                    "domain": ".instagram.com",
                    "path": "/",
                },
            ])
            self.page.goto("https://www.instagram.com/", wait_until="networkidle")
            self.page.wait_for_timeout(5000)

            # Dismiss any dialogs (Save Info, notifications, etc.)
            for text in ["Not Now", "Not now", "Save Info", "Save info", "Cancel"]:
                try:
                    btn = self.page.get_by_role("button", name=text)
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        logger.info("Dismissed dialog: %s", text)
                        self.page.wait_for_timeout(2000)
                except Exception:
                    continue

            logger.info("Session login complete for %s", self.username)
            return

        # --- Form-based login ---
        logger.info("Opening Instagram login page...")
        self.page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")

        # Dismiss cookie banner if present
        for text in ["Allow essential and optional cookies", "Allow all cookies", "Accept All", "Accept"]:
            try:
                btn = self.page.get_by_text(text, exact=False)
                if btn.is_visible(timeout=2000):
                    btn.click()
                    self.page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

        # Enter credentials
        logger.info("Entering credentials for %s", self.username)
        self.page.fill("input[name='username']", self.username)
        self.page.fill("input[name='password']", self.password)
        self.page.wait_for_timeout(500)

        # Click login
        logger.info("Clicking login button...")
        self.page.get_by_role("button", name="Log in").click()

        # Wait for navigation
        logger.info("Waiting for login to complete...")
        self.page.wait_for_timeout(8000)

        current_url = self.page.url
        logger.info("Current URL: %s", current_url)

        # Dismiss post-login dialogs
        for text in ["Save Your Login Info", "Not Now", "Not now", "Cancel"]:
            try:
                btn = self.page.get_by_text(text, exact=False)
                if btn.is_visible(timeout=3000):
                    btn.click()
                    self.page.wait_for_timeout(2000)
            except Exception:
                continue

        logger.info("Login complete for %s", self.username)

    def upload_post(self, post: dict, assets_dir: Path, hash_tags: str = "") -> bool:
        """Upload a single image post via the browser.

        Returns True on success, False on failure.
        Updates post dict in-place with posted_on or error.
        """
        file_name = post.get("file_name")
        if not file_name:
            logger.warning("No file_name for post %s — skipping", post.get("id"))
            return False

        asset_path = assets_dir / file_name
        if not asset_path.exists():
            logger.error("Asset file not found: %s", asset_path)
            post["error"] = "Asset file not found"
            return False

        ext = asset_path.suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            logger.warning("Browser upload only supports images, skipping: %s", ext)
            return False

        caption = (post.get("title") or "") + hash_tags

        try:
            logger.info("Uploading: %s", caption[:80])

            # Step 1: Click the + (create) button in bottom nav
            create_btn = self.page.get_by_role("navigation").get_by_role("link", name="Home")
            create_btn.click()
            self.page.wait_for_timeout(2000)

            # Step 2: Click "Post" — this opens the file chooser
            # Use expect_file_chooser to intercept the native file dialog
            with self.page.expect_file_chooser() as fc_info:
                self.page.get_by_text("Post", exact=True).first.click()
            file_chooser = fc_info.value
            file_chooser.set_files(str(asset_path.resolve()))
            logger.info("File selected, waiting for editor...")
            self.page.wait_for_timeout(4000)

            # Handle aspect ratio — expand if available
            for text in ["Expand", "Original", "Select crop"]:
                try:
                    btn = self.page.get_by_text(text, exact=False)
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        self.page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # Click Next (crop → caption or filters)
            self._click_by_text("Next")
            logger.info("Clicked Next")
            self.page.wait_for_timeout(2000)

            # Click Next again if there's a filters step (mobile may skip this)
            try:
                next_btn = self.page.get_by_role("button", name="Next")
                if next_btn.is_visible(timeout=2000):
                    next_btn.click()
                    logger.info("Clicked Next (filters → caption)")
                    self.page.wait_for_timeout(2000)
            except Exception:
                pass

            # Enter caption
            caption_field = self.page.locator("textarea[aria-label='Write a caption…']")
            caption_field.click()
            caption_field.fill(caption)
            logger.info("Caption entered")
            self.page.wait_for_timeout(1000)

            # Click Share (it's a <button> in the header)
            self.page.locator("button:has-text('Share')").click()
            logger.info("Sharing post...")
            self.page.wait_for_timeout(10000)

            post["posted_on"] = datetime.now().isoformat()
            logger.info("✓ Uploaded: %s", post.get("title", "")[:60])
            self.page.wait_for_timeout(2000)
            return True

        except Exception as e:
            post["error"] = str(e)
            logger.error("Error uploading post: %s", e)
            return False

    def close(self) -> None:
        """Close the browser."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # ----- Private helpers -----

    def _click_by_text(self, text: str) -> None:
        """Click a button by its accessible name."""
        self.page.get_by_role("button", name=text).click()

