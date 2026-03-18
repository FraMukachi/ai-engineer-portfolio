import requests

# Calling a real public API
response = requests.get("https://api.github.com/users/FraMukachi")

# The response comes back as a dictionary
data = response.json()

print(f"Username: {data['login']}")
print(f"Profile: {data['html_url']}")
print(f"Public repos: {data['public_repos']}")
print(f"Followers: {data['followers']}")