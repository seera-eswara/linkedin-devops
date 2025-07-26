def is_devops_related(text):
    keywords = [
        "DevOps", "CI/CD", "Kubernetes", "Docker", "Terraform", 
        "Ansible", "GitHub Actions", "Jenkins", "SRE", "Infrastructure as Code"
    ]
    return any(kw.lower() in text.lower() for kw in keywords)
