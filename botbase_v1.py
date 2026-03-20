from groq import Groq
import os
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# BotBase v1 — AI Customer Support Bot
# This is the core engine every business will use

class BotBase:
    def __init__(self, business_name, business_info):
        self.business_name = business_name
        self.business_info = business_info
        self.conversation_history = []

    def chat(self, user_message):
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"""You are a helpful customer support assistant for {self.business_name}.

Business Information:
{self.business_info}

Rules:
- Only answer questions about this business
- Be friendly and professional
- If you don't know something, say 'Let me connect you with our team for that.'
- Keep answers short and helpful
- Never make up information not provided above"""},
            ] + self.conversation_history
        )

        ai_response = response.choices[0].message.content
        self.conversation_history.append({
            "role": "assistant",
            "content": ai_response
        })
        return ai_response

# Demo — Pizza Restaurant
pizza_info = """
Business: Pizza Palace
Location: Cape Town, South Africa
Phone: 021-555-1234
Hours: Mon-Sun 11am to 10pm

Menu:
- Margherita Pizza: R89
- Pepperoni Pizza: R99
- Veggie Pizza: R85
- Chicken BBQ Pizza: R109
- Large size add R30

Delivery:
- Free delivery over R200
- Delivery fee R25 under R200
- Delivery time: 30-45 minutes
- Delivery radius: 10km

Specials:
- Monday: Buy 2 get 1 free
- Wednesday: 20% off all pizzas
- Student discount: 15% with valid student card
"""

bot = BotBase("Pizza Palace", pizza_info)

# Simulate customer conversation
questions = [
    "Hi, what are your hours?",
    "How much is a pepperoni pizza?",
    "Do you deliver to me? I'm 8km away",
    "Any specials today? It's Wednesday",
    "What's the cheapest pizza you have?"
]

print("=== BOTBASE V1 — PIZZA PALACE ===\n")
for question in questions:
    print(f"Customer: {question}")
    response = bot.chat(question)
    print(f"Bot: {response}\n")
