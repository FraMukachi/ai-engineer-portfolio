from groq import Groq
import os
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MEMORY_FILE = "ai_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"facts": [], "summary": ""}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

def update_memory(conversation, memory):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """Extract key facts about the user from this conversation.
Return ONLY a JSON object like this:
{"facts": ["fact1", "fact2"], "summary": "one sentence summary"}
No explanation. No markdown."""},
            {"role": "user", "content": str(conversation)}
        ]
    )
    try:
        extracted = json.loads(response.choices[0].message.content)
        memory["facts"].extend(extracted["facts"])
        memory["facts"] = list(set(memory["facts"]))
        memory["summary"] = extracted["summary"]
        save_memory(memory)
    except:
        pass
    return memory

def chat(user_message, memory):
    memory_context = f"Facts about user: {memory['facts']}" if memory["facts"] else ""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"""You are a helpful assistant with permanent memory.
{memory_context}
Use what you know about the user to personalize responses."""},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

# Session 1 — tell the AI about yourself
memory = load_memory()
print("=== SESSION 1 ===")
response1 = chat("My name is Fra. I am a Full Stack developer from South Africa learning AI Engineering.", memory)
print(f"AI: {response1}")

conversation = [
    {"role": "user", "content": "My name is Fra. I am a Full Stack developer from South Africa learning AI Engineering."},
    {"role": "assistant", "content": response1}
]
memory = update_memory(conversation, memory)
print(f"\nMemory saved: {memory['facts']}")

# Session 2 — new session, AI still remembers
print("\n=== SESSION 2 (new session, fresh start) ===")
memory = load_memory()
response2 = chat("What do you know about me?", memory)
print(f"AI: {response2}")
