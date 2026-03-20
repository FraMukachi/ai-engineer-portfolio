from groq import Groq
import os
import chromadb
from sentence_transformers import SentenceTransformer

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("botbase")

# Business documents — this would come from uploaded files
documents = [
    "Pizza Palace is located in Cape Town, South Africa. Phone: 021-555-1234. Open Monday to Sunday 11am to 10pm.",
    "Our menu includes Margherita Pizza R89, Pepperoni Pizza R99, Veggie Pizza R85, Chicken BBQ Pizza R109. Large size add R30.",
    "Delivery is free for orders over R200. Orders under R200 have a R25 delivery fee. Delivery takes 30-45 minutes within 10km.",
    "Monday special: Buy 2 get 1 free. Wednesday special: 20% off all pizzas. Students get 15% off with valid student card.",
    "We accept cash, card, and EFT payments. No cheques accepted. Online orders available on our website.",
    "Allergen info: Margherita contains gluten and dairy. Veggie pizza is vegetarian. We cannot guarantee nut-free environment.",
]

# Index documents
print("Indexing documents...")
embeddings = embedding_model.encode(documents).tolist()
collection.add(
    documents=documents,
    embeddings=embeddings,
    ids=[f"doc_{i}" for i in range(len(documents))]
)
print(f"Indexed {len(documents)} documents\n")

def ask_botbase(question):
    # Find relevant documents
    question_embedding = embedding_model.encode([question]).tolist()
    results = collection.query(query_embeddings=question_embedding, n_results=2)
    relevant_docs = results["documents"][0]
    context = "\n".join(relevant_docs)

    # Ask AI with context
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"""You are a customer support bot for Pizza Palace.
Answer questions using ONLY this information:
{context}
If the answer is not in the information, say you don't have that info."""},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

# Test questions
questions = [
    "Do you deliver and how much does it cost?",
    "What allergens are in the Margherita pizza?",
    "Do you have student discounts?",
    "What payment methods do you accept?"
]

print("=== BOTBASE WITH RAG ===\n")
for q in questions:
    print(f"Customer: {q}")
    print(f"Bot: {ask_botbase(q)}\n")
