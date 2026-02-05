# app/api/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.gcp_storage import gcs_storage

router = APIRouter()

# 設定允許的檔案格式與大小限制 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/webp"}

@router.post("/")
async def upload_image(file: UploadFile = File(...)):
    """
    接收前端上傳的圖片，並轉傳至 GCP Cloud Storage
    """

    # 1. 檢查檔案格式
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支援的檔案格式。僅限: {ALLOWED_EXTENSIONS}"
        )

    # 2. 檢查檔案大小
    # 讀取檔案內容來確認大小
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="檔案太大了，不能超過 5MB"
        )
    
    # 因為剛剛執行了 file.read()，檔案指針移到了最後面
    # 我們必須把它移回開頭，否則上傳會變成空檔案
    await file.seek(0)

    # 3. 呼叫我們封裝好的 GCP 工具進行上傳
    # 我們這裡指定存放在 "coffee-images" 資料夾下
    file_url = gcs_storage.upload_file(file, folder="coffee-images")

    if not file_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="上傳至雲端失敗，請稍後再試"
        )

    # 4. 回傳成功的結果與圖片網址
    return {
        "message": "上傳成功",
        "image_url": file_url,
        "filename": file.filename
    }