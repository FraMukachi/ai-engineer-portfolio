from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def ask_with_system(system_prompt, user_message):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

# Same question, different system prompts = completely different answers

print("=== AS A PIRATE ===")
print(ask_with_system(
    "You are a pirate. Respond to everything in pirate speak.",
    "What is Python?"
))

print("\n=== AS A SENIOR ENGINEER ===")
print(ask_with_system(
    "You are a senior software engineer with 10 years experience. Give concise technical answers. No fluff.",
    "What is Python?"
))

print("\n=== AS A CAREER COACH ===")
print(ask_with_system(
    "You are a career coach specializing in tech. You help developers from Africa break into high paying tech roles. Be motivating and practical.",
    "I am a Full Stack developer from South Africa learning AI Engineering. What should I focus on?"
))
