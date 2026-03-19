import requests
import os

# Classes — organizing your code into reusable objects
# Think of a class as a blueprint

class GitHubUser:
    def __init__(self, username):
        self.username = username
        self.data = None

    def fetch(self):
        try:
            response = requests.get(f"https://api.github.com/users/{self.username}")
            if response.status_code == 200:
                self.data = response.json()
                print(f"Fetched data for {self.username}")
            else:
                print(f"User not found: {self.username}")
        except Exception as e:
            print(f"Error: {e}")

    def summary(self):
        if not self.data:
            print("No data. Run fetch() first.")
            return
        print(f"Username: {self.data['login']}")
        print(f"Repos: {self.data['public_repos']}")
        print(f"Followers: {self.data['followers']}")
        print(f"Profile: {self.data['html_url']}")

    def is_active(self):
        if not self.data:
            return False
        return self.data['public_repos'] > 0

# Using the class
user = GitHubUser("FraMukachi")
user.fetch()
user.summary()
print(f"Is active: {user.is_active()}")
