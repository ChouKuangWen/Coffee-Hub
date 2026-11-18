"""僅在顯式呼叫時建立 GCS Client；匯入不讀憑證、不連雲端。"""
from google.cloud import storage
from google.api_core.exceptions import NotFound
from datetime import datetime, timezone


class GCPStorage:
    def __init__(self):
        self.client = None

    def _blob(self, bucket, object_name):
        if self.client is None:
            self.client = storage.Client()
        return self.client.bucket(bucket).blob(object_name)

    def upload_bytes(self, bucket, object_name, contents, content_type, image_id, sha256):
        blob = self._blob(bucket, object_name)
        blob.metadata = {"coffeehub_image_id": image_id, "sha256": sha256}
        # 隨機新物件；絕不覆寫既有 generation。
        blob.upload_from_string(contents, content_type=content_type, if_generation_match=0, timeout=60)
        return int(blob.generation)

    def inspect_object(self, bucket, object_name):
        blob = self._blob(bucket, object_name)
        try:
            blob.reload(timeout=30)
        except NotFound:
            return None
        expiry = blob.retention_expiration_time
        return {"generation": int(blob.generation), "metadata": blob.metadata or {},
                "held": bool(blob.temporary_hold or blob.event_based_hold
                             or (expiry is not None and expiry > datetime.now(timezone.utc)))}

    def delete_generation(self, bucket, object_name, generation):
        blob = self._blob(bucket, object_name)
        try:
            blob.delete(if_generation_match=generation, timeout=30)
        except NotFound:
            pass


gcs_storage = GCPStorage()
