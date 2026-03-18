from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
        return {"message": "Hello Fra"}

        @app.get("/status")
        def status():
                return {"status": "live"}