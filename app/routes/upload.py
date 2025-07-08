# app/routes/upload.py

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from datetime import datetime
from app.services.s3_client import create_presigned_url, upload_file_to_s3
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


# ─── Direct Upload Endpoint ──────────────────────────────────

@router.post("/file", response_model=UploadCompleteResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file directly through the backend to avoid CORS issues.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate a unique key for the file
        import uuid
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        key = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
        
        # Upload to S3
        success = await upload_file_to_s3(file_content, key)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")
        
        # Record in MongoDB
        recorded_time = datetime.utcnow()
        doc = {
            "key": key,
            "filename": file.filename,
            "recorded_at": recorded_time
        }
        
        await db.uploads.insert_one(doc)
        
        return UploadCompleteResponse(**doc)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
