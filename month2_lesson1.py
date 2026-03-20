from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

print("Calling Groq API...")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "Hello! I am Fra, a Full Stack developer from South Africa learning AI Engineering. Give me a one paragraph welcome message."}
    ]
)

print("\nGroq says:")
print(response.choices[0].message.content)
