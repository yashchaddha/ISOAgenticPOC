# app/routes/upload.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from app.services.s3_client import create_presigned_url
from app.services.mongo_client import db
from typing import List

router = APIRouter()


# ─── Presign Endpoint ─────────────────────────────────────────────

class PresignRequest(BaseModel):
    filename: str

class PresignResponse(BaseModel):
    upload_url: str
    key: str

@router.post("/presign", response_model=PresignResponse)
async def presign_upload(req: PresignRequest):
    """
    Generate a presigned PUT URL so the client can upload directly to S3.
    """
    key = req.filename  # store at bucket root
    try:
        url = create_presigned_url(key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate presigned URL: {e}")
    return PresignResponse(upload_url=url, key=key)


# ─── Upload-Complete Endpoint ────────────────────────────────────

class UploadCompleteRequest(BaseModel):
    key: str
    filename: str

class UploadCompleteResponse(BaseModel):
    key: str
    filename: str
    recorded_at: datetime

@router.post("/complete", response_model=UploadCompleteResponse)
async def complete_upload(req: UploadCompleteRequest):
    """
    Record the uploaded file’s metadata in MongoDB.
    """
    recorded_time = datetime.utcnow()
    doc = {
        "key": req.key,
        "filename": req.filename,
        "recorded_at": recorded_time
    }
    try:
        await db.uploads.insert_one(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not record upload metadata: {e}")
    return UploadCompleteResponse(**doc)


@router.get("/all", response_model=List[UploadCompleteResponse])
async def list_uploads():
    """
    Return all uploaded-file records from MongoDB.
    """
    docs = await db.uploads.find().to_list(length=100)
    # Transform Mongo documents into the Pydantic model
    return [
        UploadCompleteResponse(
            key=d["key"],
            filename=d["filename"],
            recorded_at=d["recorded_at"]
        )
        for d in docs
    ]
