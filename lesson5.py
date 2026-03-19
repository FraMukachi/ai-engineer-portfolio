import os

# Environment variables — storing secrets safely
# Never put API keys directly in your code

# Setting an environment variable (normally done outside the code)
os.environ["MY_NAME"] = "Fra"
os.environ["MY_COUNTRY"] = "South Africa"

# Reading environment variables
name = os.environ.get("MY_NAME")
country = os.environ.get("MY_COUNTRY")

# Safe way — provide a default if not found
api_key = os.environ.get("API_KEY", "not set")

print(f"Name: {name}")
print(f"Country: {country}")
print(f"API Key: {api_key}")

# Why this matters — wrong way vs right way
# WRONG - never do this:
# api_key = "sk-ant-1234567890abcdef"

# RIGHT - always do this:
# api_key = os.environ.get("ANTHROPIC_API_KEY")

print("\nIn Month 2 you will do this:")
print('api_key = os.environ.get("ANTHROPIC_API_KEY")')
print("That keeps your key out of GitHub and safe.")
