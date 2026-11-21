from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from multiprocessing import get_context

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.documents import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # O PyMuPDF não é seguro para uso concorrente em threads.
    with ProcessPoolExecutor(max_workers=1, mp_context=get_context("spawn")) as executor:
        app.state.pdf_executor = executor
        yield


app = FastAPI(
    lifespan=lifespan,
    title="PDF Data Extractor API",
    description="API para extração e processamento de documentos PDF.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://{host}:{port}"
        for host in ("localhost", "127.0.0.1")
        for port in (5173, 4173)
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "pdf-data-extractor",
        "version": app.version,
    }


app.include_router(documents_router)
