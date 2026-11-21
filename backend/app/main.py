
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PDF Data Extractor API",
    description="API para extração e processamento de documentos PDF.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "pdf-data-extractor",
        "version": "1.0.0",
    }
