import os
import uuid
from datetime import datetime
from google.cloud import storage

# BUCKET名稱放在環境變數中，方便雲端與本地切換
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

class GCPStorage:
    def __init__(self):
        """
        1. 本地開發：用環境變數 GOOGLE_APPLICATION_CREDENTIALS 指向的 JSON。
        2. 雲端環境：自動使用 Cloud Run 的執行身分 (Service Account)。
        """
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(BUCKET_NAME)
            print(f"成功連線至 GCS Bucket: {BUCKET_NAME}")
        except Exception as e:
            print(f"GCP Storage 連線失敗: {e}")

    def upload_file(self, file_obj, folder="products"):
        try:
            # 生成唯一檔名
            ext = os.path.splitext(file_obj.filename)[1]
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
            blob_path = f"{folder}/{unique_filename}"
            blob = self.bucket.blob(blob_path)
            
            # 上傳檔案流
            blob.upload_from_file(
                file_obj.file,
                content_type=file_obj.content_type
            )

            # 回傳網址
            return f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
        
        except Exception as e:
            print(f"上傳錯誤: {e}")
            return None

# 實例化物件
gcs_storage = GCPStorage()