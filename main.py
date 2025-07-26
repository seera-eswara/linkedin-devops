import os
import re
import time
import logging
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Email settings - replace with your credentials or load from environment variables
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use Gmail App Password, NOT your normal password
EMAIL_RECEIVER = "recipient_email@example.com"

# LinkedIn browser session directory (persistent session)
SESSION_PATH = os.path.join(os.getcwd(), "user-data-dir")

# DevOps keywords for filtering posts
KEYWORDS = [
    "devops", "ci/cd", "docker", "kubernetes", "terraform",
    "jenkins", "github actions", "infrastructure as code",
    "cloud engineer", "sre", "ansible", "helm", "prometheus", "grafana",
    "aws", "azure", "gcp"
]

# How many times to scroll down to load older posts
MAX_SCROLLS = 10

# Delay between scrolls in seconds
SCROLL_DELAY = 3


def is_devops_related(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in KEYWORDS)


def parse_relative_time(text: str) -> datetime | None:
    """
    Parse LinkedIn relative time like '1 hour ago', '3 days ago', 'Just now' to datetime.
    Returns None if parsing fails.
    """
    text = text.lower()
    now = datetime.now()

    if "just now" in text:
        return now

    match = re.match(r"(\d+)\s+(minute|hour|day|week)s?\s+ago", text)
    if match:
        num = int(match.group(1))
        unit = match.group(2)

        if unit == "minute":
            return now - timedelta(minutes=num)
        elif unit == "hour":
            return now - timedelta(hours=num)
        elif unit == "day":
            return now - timedelta(days=num)
        elif unit == "week":
            return now - timedelta(weeks=num)

    # Sometimes text could be '1 mo ago' or a date string, but skipping for simplicity
    return None


def send_email(subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def scroll_feed(page, max_scrolls=MAX_SCROLLS, delay=SCROLL_DELAY):
    """Scroll down the LinkedIn feed to load more posts."""
    last_height = page.evaluate("() => document.body.scrollHeight")
    logging.info(f"Initial scroll height: {last_height}")
    for i in range(max_scrolls):
        logging.info(f"Scrolling down: {i + 1}/{max_scrolls}")
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay)
        new_height = page.evaluate("() => document.body.scrollHeight")
        logging.info(f"New scroll height: {new_height}")

        if new_height == last_height:
            logging.info("Reached bottom of feed (no more scroll).")
            break
        last_height = new_height


def extract_posts():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False  # Change to True once you confirm it works
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.linkedin.com/feed/")
        page.wait_for_timeout(7000)  # Wait initial load

        # Scroll down to load more posts
        scroll_feed(page)

        posts = page.query_selector_all("div.feed-shared-update-v2")
        logging.info(f"Total posts found after scrolling: {len(posts)}")

        filtered_posts = []
        four_days_ago = datetime.now() - timedelta(days=4)

        for post in posts:
            try:
                content_element = post.query_selector("span.break-words")
                timestamp_element = post.query_selector("span.feed-shared-actor__sub-description")

                if not content_element or not timestamp_element:
                    continue

                content = content_element.inner_text().strip()
                timestamp_text = timestamp_element.inner_text().strip()
                post_time = parse_relative_time(timestamp_text)

                if post_time and post_time >= four_days_ago:
                    if is_devops_related(content):
                        filtered_posts.append(f"[{timestamp_text}] {content}")
                        logging.info(f"DevOps post found: {content[:80]}...")
                else:
                    logging.debug(f"Ignored post older than 4 days: {timestamp_text}")

            except Exception as e:
                logging.warning(f"Error processing a post: {e}")
                continue

        browser.close()
        return filtered_posts


def main():
    posts = extract_posts()
    if posts:
        email_body = "\n\n---\n\n".join(posts)
        send_email("LinkedIn DevOps Posts - Last 4 Days", email_body)
    else:
        logging.info("No DevOps posts found in the last 4 days.")
        send_email("LinkedIn DevOps Posts - Last 4 Days", "No relevant DevOps posts found in the last 4 days.")


if __name__ == "__main__":
    main()
