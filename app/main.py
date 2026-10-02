from  fastapi import FastAPI
from core.db import init_db
from fastapi.middleware.cors import CORSMiddleware
from index_controller import api_router

async def lifespan(app:FastAPI):
    await init_db()
    print("Database connect")
    yield
    print("Shutting down the app")



app = FastAPI(
    title ="Document Analyser API",
    description = "AI Powered Document Analysis."
)


# CORS FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],       
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")


@app.get('/')
def root():
    return {
        "app" : "Document Analyser",
        "versoin" :"1.0.0",
    }


