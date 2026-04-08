# app/schemas/upload.py
from pydantic import BaseModel

class UploadResponse(BaseModel):
    message: str
    image_url: str
    filename: str