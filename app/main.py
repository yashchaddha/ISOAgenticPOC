from fastapi import FastAPI
from app.config import settings
import logging
from app.services.mongo_client import db
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routes.upload import router as upload_router
from app.routes.audit import router as audit_router

from dotenv import load_dotenv
load_dotenv()




app = FastAPI(title="ISO27001 Auditor")
logging.getLogger("uvicorn").info(f"🐘 Loaded settings: {settings.dict()!r}")

origins = [
    "http://localhost:3000",   # React dev server
    # add any other domains (e.g. your production URL) here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # you can use ["*"] to allow all, but be cautious in prod
    allow_credentials=True,
    allow_methods=["*"],          # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],          # allow all headers (e.g. Content-Type, Authorization)
)

app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(audit_router)

@app.get("/")
async def root():
    return {"message": "API is up and running!"}

@app.get("/health/db")
async def db_health_check():
    try:
        # This will throw if the server is unreachable
        await db.list_collection_names()
        return {"status": "MongoDB connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {e}")
    
logging.getLogger("uvicorn").info(f"🐘 AWS_REGION = {settings.aws_region!r}")

logging.getLogger("uvicorn").info(f"Loaded settings: {settings.dict(exclude={'mongodb_uri'})}")
