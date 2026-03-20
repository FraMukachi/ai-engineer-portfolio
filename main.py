from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import groq
import os
import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from docx import Document
import io
import uuid

app = FastAPI(title="BotBase API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()

businesses = {}

def extract_text(file_bytes, filename):
    if filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join([page.extract_text() for page in reader.pages])
    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return file_bytes.decode("utf-8")

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

@app.get("/")
def home():
    return {
        "product": "BotBase",
        "version": "2.0",
        "status": "live",
        "endpoints": {
            "upload": "POST /upload",
            "chat": "POST /chat",
            "businesses": "GET /businesses"
        }
    }

@app.post("/upload")
async def upload_document(
    business_name: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        file_bytes = await file.read()
        text = extract_text(file_bytes, file.filename)
        chunks = chunk_text(text)

        business_id = business_name.lower().replace(" ", "_")

        if business_id not in businesses:
            businesses[business_id] = {
                "name": business_name,
                "collection": chroma_client.create_collection(f"bot_{business_id}_{uuid.uuid4().hex[:8]}")
            }

        collection = businesses[business_id]["collection"]
        embeddings = embedding_model.encode(chunks).tolist()
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=[f"chunk_{i}" for i in range(len(chunks))]
        )

        return {
            "status": "success",
            "business": business_name,
            "business_id": business_id,
            "chunks_indexed": len(chunks),
            "message": f"Bot ready for {business_name}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/chat")
async def chat(
    business_id: str = Form(...),
    message: str = Form(...)
):
    try:
        if business_id not in businesses:
            return {"status": "error", "message": "Business not found. Upload documents first."}

        collection = businesses[business_id]["collection"]
        business_name = businesses[business_id]["name"]

        question_embedding = embedding_model.encode([message]).tolist()
        results = collection.query(query_embeddings=question_embedding, n_results=3)
        context = "\n".join(results["documents"][0])

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"""You are a customer support assistant for {business_name}.
Answer questions using ONLY this information:
{context}
If the answer is not in the information provided, say: 'I don't have that information. Please contact us directly.'
Be friendly, helpful and concise."""},
                {"role": "user", "content": message}
            ]
        )

        return {
            "status": "success",
            "business": business_name,
            "response": response.choices[0].message.content
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/businesses")
def list_businesses():
    return {
        "total": len(businesses),
        "businesses": [
            {"id": bid, "name": bdata["name"]}
            for bid, bdata in businesses.items()
        ]
    }
