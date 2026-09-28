import fastapi as fastAPI
import os

app = fastAPI.FastAPI()

@app.get("/")
def root():
    return {"message": "Привет, Всем!"}

