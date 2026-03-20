from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
import uuid

app = FastAPI(title="BotBase API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
businesses = {}

def extract_text(file_bytes, filename):
    if filename.endswith(".pdf"):
        import pypdf, io
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return "\n".join([page.extract_text() for page in reader.pages])
    elif filename.endswith(".docx"):
        from docx import Document
        import io
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return file_bytes.decode("utf-8")

def chunk_text(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def find_relevant_chunks(question, chunks, top_n=3):
    question_words = set(question.lower().split())
    scored = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        score = len(question_words & chunk_words)
        scored.append((score, chunk))
    scored.sort(reverse=True)
    return [chunk for _, chunk in scored[:top_n]]

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
        businesses[business_id] = {
            "name": business_name,
            "chunks": chunks
        }
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

        business_name = businesses[business_id]["name"]
        chunks = businesses[business_id]["chunks"]
        relevant = find_relevant_chunks(message, chunks)
        context = "\n".join(relevant)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"""You are a customer support assistant for {business_name}.
Answer using ONLY this information:
{context}
If the answer is not here, say: 'I don't have that info. Please contact us directly.'
Be friendly and concise."""},
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
