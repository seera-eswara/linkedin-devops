import re

DEVOPS_KEYWORDS = [
    "devops", "ci/cd", "docker", "kubernetes", "terraform",
    "jenkins", "github actions", "infrastructure as code",
    "cloud engineer", "sre", "ansible", "helm", "prometheus", "grafana"
]

def is_devops_related(text):
    # Lowercase everything
    clean_text = text.lower()

    # Skip if it's mostly hashtags
    if clean_text.count("#") > 10 and len(clean_text.split()) < 50:
        return False

    # Remove hashtags for better matching
    text_no_hashtags = re.sub(r"#\S+", "", clean_text)

    # Return True if devops keywords appear in meaningful content
    return any(kw in text_no_hashtags for kw in DEVOPS_KEYWORDS)
