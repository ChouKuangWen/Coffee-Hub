# app/schemas/upload.py
from pydantic import BaseModel, ConfigDict, Field

class UploadResponse(BaseModel):
    message: str
    image_url: str
    filename: str
    image_id: str


class ImageCleanupRequest(BaseModel):
    dry_run: bool = True
    limit: int = Field(10, ge=1, le=20)
    model_config = ConfigDict(extra="forbid")
