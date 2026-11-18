from fastapi import APIRouter, UploadFile, File, Form, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db
from app.dependencies import get_current_user_from_cookie, has_permission
from app.schemas.upload import UploadResponse, ImageCleanupRequest
from app.services.image_service import upload_product_image, process_image_cleanup, MAX_BYTES
from app.core.rate_limit import limiter

router = APIRouter()


@router.post("/", response_model=UploadResponse, dependencies=[Depends(has_permission([1, 2]))])
@limiter.limit("10/minute")
@limiter.limit("10/minute", key_func=lambda request: f"image-user:{getattr(request.state, 'user_id', 'anonymous')}")
async def upload_image(request: Request, product_id: int = Form(..., gt=0), file: UploadFile = File(...),
                        db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user_from_cookie)):
    # 有界讀取，禁止把超大檔案一次讀入記憶體；服務端解碼與 GCS IO 不阻塞 event loop。
    try:
        contents = await file.read(MAX_BYTES + 1)
        return await upload_product_image(db, request, current_user, product_id, contents, file.content_type)
    finally:
        await file.close()


@router.post("/cleanup", dependencies=[Depends(has_permission([1]))])
@limiter.limit("2/minute")
async def cleanup_images(request: Request, data: ImageCleanupRequest,
                          db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user_from_cookie)):
    return await process_image_cleanup(db, request, current_user, data.dry_run, data.limit)
