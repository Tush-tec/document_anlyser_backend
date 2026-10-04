import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.db import init_db
from index_controller import api_router
from service import ingest, vector_store

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                                   # sync function: no `await`
    vector_store.ensure_collection_sync()       # creates the Qdrant collection + indexes
    stuck = ingest.recover_stuck_documents()    # fail documents orphaned by a restart
    
    from service import embedder
    embedder._model()   # or expose a warmup() function
    logging.info("Embedding model loaded")

    print(f"Startup complete. Recovered {stuck} stuck document(s).")
    yield
    print("Shutting down the app")


app = FastAPI(
    title="Document Analyser API",
    description="AI Powered Document Analysis.",
    lifespan=lifespan,                          # without this line, startup code never runs
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"app": "Document Analyser", "version": "1.0.0"}