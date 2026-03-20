from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Conversation memory — AI remembers what you said earlier
conversation_history = []

def chat(user_message):
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Send full history every time
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant. Be concise."},
        ] + conversation_history
    )

    # Get AI response
    ai_message = response.choices[0].message.content

    # Add AI response to history
    conversation_history.append({
        "role": "assistant",
        "content": ai_message
    })

    return ai_message

# Multi-turn conversation — AI remembers everything
print("Turn 1:")
print(chat("My name is Fra and I live in South Africa."))

print("\nTurn 2:")
print(chat("What is my name and where do I live?"))

print("\nTurn 3:")
print(chat("What career am I likely pursuing based on the context of our conversation?"))

print("\nFull conversation history:")
for msg in conversation_history:
    print(f"{msg['role'].upper()}: {msg['content'][:80]}...")
