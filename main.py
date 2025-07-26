from playwright.sync_api import sync_playwright
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
from devops_filter import is_devops_related
from email_utils import send_email
import time

def extract_posts():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.linkedin.com/login")

        page.fill("input[name='session_key']", LINKEDIN_EMAIL)
        page.fill("input[name='session_password']", LINKEDIN_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)

        page.goto("https://www.linkedin.com/feed/")
        time.sleep(5)
        posts = page.query_selector_all(".update-components-text")

        results = []
        for post in posts:
            try:
                content = post.inner_text()
                if is_devops_related(content):
                    results.append(content)
            except:
                continue

        browser.close()
        return results

def clean_post(post):
    # Remove all hashtags and trim long content
    post = re.sub(r"#\S+", "", post)
    return post.strip()[:600]

def main():
    posts = extract_posts()
    posts = [clean_post(p) for p in posts]
    content = "\n\n---\n\n".join(posts)
    if posts:
        content = "\n\n---\n\n".join(posts)
        send_email("📣 DevOps Posts from LinkedIn Feed", content)
    else:
        print("No DevOps posts found.")

if __name__ == "__main__":
    main()
