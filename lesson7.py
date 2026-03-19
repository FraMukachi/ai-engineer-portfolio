import requests
import json
from datetime import datetime

class GitHubAnalyzer:
    def __init__(self, username):
        self.username = username
        self.data = None
        self.report = None

    def fetch(self):
        try:
            response = requests.get(f"https://api.github.com/users/{self.username}")
            if response.status_code == 200:
                self.data = response.json()
                return True
            else:
                print(f"User not found: {self.username}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def analyze(self):
        if not self.data:
            return None
        repos = self.data['public_repos']
        if repos >= 20:
            level = "Advanced"
        elif repos >= 10:
            level = "Intermediate"
        elif repos >= 3:
            level = "Beginner"
        else:
            level = "Just starting"
        self.report = {
            "username": self.data['login'],
            "repos": repos,
            "followers": self.data['followers'],
            "level": level,
            "profile_url": self.data['html_url'],
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.report

    def save_report(self):
        filename = f"{self.username}_report.json"
        with open(filename, "w") as f:
            json.dump(self.report, f, indent=4)
        print(f"Report saved to {filename}")

    def print_report(self):
        print("\n=== GitHub Profile Report ===")
        for key, value in self.report.items():
            print(f"{key}: {value}")

analyzer = GitHubAnalyzer("FraMukachi")
if analyzer.fetch():
    analyzer.analyze()
    analyzer.print_report()
    analyzer.save_report()
