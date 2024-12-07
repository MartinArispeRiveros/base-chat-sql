from fastapi import FastAPI
from app.api.v1.endpoints import router

app = FastAPI(
    title="RAG system",
    description="",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG system"}