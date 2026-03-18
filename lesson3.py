import requests

# If statements
age = 20

if age >= 18:
    print("You can access this app")
else:
    print("You are too young")

# If / elif / else
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "Fail"

print(f"Your grade is: {grade}")

# Error handling
def get_github_user(username):
    try:
        response = requests.get(f"https://api.github.com/users/{username}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found user: {data['login']}")
            print(f"Repos: {data['public_repos']}")
        elif response.status_code == 404:
            print(f"User {username} not found")
        else:
            print(f"Something went wrong: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

get_github_user("FraMukachi")
get_github_user("thisuserdoesnotexist99999")
