from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def ask(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# BAD prompt - vague
print("=== BAD PROMPT ===")
print(ask("tell me about python"))

print("\n=== GOOD PROMPT ===")
print(ask("""
You are a coding teacher. 
Explain Python in exactly 3 bullet points.
Each bullet must be one sentence.
Use simple language for a beginner.
"""))

print("\n=== SPECIFIC OUTPUT PROMPT ===")
print(ask("""
Generate a JSON object for a developer profile with these fields:
- name: Fra
- country: South Africa
- skills: list of 3 AI engineering skills
- level: beginner/intermediate/advanced

Return ONLY the JSON. No explanation. No markdown.
"""))
