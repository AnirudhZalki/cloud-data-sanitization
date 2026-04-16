# server reload trigger
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid
import os
import httpx
from services.ml_processor import process_file_content
from services.aws_service import upload_to_s3, generate_presigned_url, INPUT_BUCKET, OUTPUT_BUCKET
from dotenv import load_dotenv

import models
import schemas
import auth
from database import engine, get_db
from services.email_service import send_sanitized_email

load_dotenv()

# Create DB tables
models.Base.metadata.create_all(bind=engine)

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_DEFAULT_REGION")

app = FastAPI(title="Data Sanitization System")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_local_store: dict = {}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Data Sanitization API"}

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role if user.role else "user"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/history", response_model=list[schemas.FileRecordResponse])
def get_history(
    current_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    records = db.query(models.FileRecord).order_by(models.FileRecord.created_at.desc()).all()
    return records

@app.get("/files/{file_id}/{file_type}")
def serve_local_file(file_id: str, file_type: str):
    entry = _local_store.get(file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found or expired")
    if file_type not in ("original", "sanitized"):
        raise HTTPException(status_code=400, detail="file_type must be 'original' or 'sanitized'")

    data = entry[f"{file_type}_bytes"]
    mime = entry["mime_type"]
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": "inline"},
    )

@app.get("/proxy")
async def proxy_file(url: str = Query(..., description="Remote URL to proxy inline")):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
        mime = r.headers.get("Content-Type", "application/octet-stream").split(";")[0]
        return Response(
            content=r.content,
            media_type=mime,
            headers={"Content-Disposition": "inline"},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to proxy file: {e}")

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    is_pdf = file.content_type == "application/pdf"
    if not file.content_type.startswith("image/") and not is_pdf:
        raise HTTPException(status_code=400, detail="Only image and PDF files are supported currently")

    try:
        file_bytes = await file.read()

        file_id = str(uuid.uuid4())
        ext = "pdf" if is_pdf else (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "png")
        mime_type = file.content_type
        original_key = f"uploads/{file_id}.{ext}"
        sanitized_key = f"sanitized/{file_id}.{ext}"

        upload_success_orig = upload_to_s3(file_bytes, INPUT_BUCKET, original_key)
        sanitized_bytes, extracted_text, sensitive_data = process_file_content(file_bytes, is_pdf=is_pdf)
        upload_success_sanitized = upload_to_s3(sanitized_bytes, OUTPUT_BUCKET, sanitized_key)

        is_connected = bool(upload_success_orig and upload_success_sanitized)

        if is_connected:
            original_url = generate_presigned_url(INPUT_BUCKET, original_key)
            sanitized_url = generate_presigned_url(OUTPUT_BUCKET, sanitized_key)
        else:
            _local_store[file_id] = {
                "original_bytes": file_bytes,
                "sanitized_bytes": sanitized_bytes,
                "mime_type": mime_type,
            }
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            original_url = f"{base_url}/files/{file_id}/original"
            sanitized_url = f"{base_url}/files/{file_id}/sanitized"

        file_record = models.FileRecord(
            user_id=current_user.id,
            file_id=file_id,
            original_filename=file.filename,
            original_url=original_url,
            sanitized_url=sanitized_url,
            file_type=mime_type
        )
        db.add(file_record)
        db.commit()

        send_sanitized_email(current_user.email, file.filename, sanitized_url)

        return {
            "file_id": file_id,
            "status": "success",
            "original_url": original_url,
            "sanitized_url": sanitized_url,
            "is_aws_connected": is_connected,
            "extracted_text": extracted_text,
            "sensitive_data": sensitive_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
