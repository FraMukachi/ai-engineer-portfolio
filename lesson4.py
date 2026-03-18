import json

# Writing data to a file
user = {
    "name": "Fra",
    "country": "South Africa",
    "skills": ["Python", "FastAPI", "AI APIs"],
    "repos": 21
}

# Save to a JSON file
with open("user_data.json", "w") as f:
    json.dump(user, f, indent=4)

print("Data saved to user_data.json")

# Reading it back
with open("user_data.json", "r") as f:
    loaded = json.load(f)

print(f"Loaded name: {loaded['name']}")
print(f"Loaded skills: {loaded['skills']}")

# Adding new data and saving again
loaded['skills'].append("Kubernetes")
loaded['learning'] = "AI Engineering"

with open("user_data.json", "w") as f:
    json.dump(loaded, f, indent=4)

print("Updated and saved.")
print(f"Skills now: {loaded['skills']}")
