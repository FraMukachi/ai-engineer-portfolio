
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello Fra, your AI engineering journey starts now."}

    @app.get("/status")
    def status():
        return {"status": "live", "engineer": "Fra Mukachi", "learning": "AI Engineering"}