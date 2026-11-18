"""圖片登記、二次授權與延遲清理；不立即補償刪除任何舊圖。"""
import hashlib
import json
import re
import logging
from datetime import datetime, timedelta, timezone
from io import BytesIO
from uuid import uuid4
from types import SimpleNamespace
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select, or_, func
from app.core.config import settings
from app.core.gcp_storage import gcs_storage
from app.models.image_asset import ImageAsset
from app.models.products import Products
from app.services.audit_log_service import record_required_action

MAX_BYTES = 5 * 1024 * 1024
FORMATS = {"JPEG": ("image/jpeg", "jpg"), "PNG": ("image/png", "png"), "WEBP": ("image/webp", "webp")}


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _grace():
    return timedelta(days=max(7, getattr(settings, "IMAGE_CLEANUP_GRACE_DAYS", 7)))


def _retry():
    return timedelta(hours=max(24, getattr(settings, "IMAGE_CLEANUP_RETRY_HOURS", 24)))


def _after(delay):
    deadline = _now() + delay
    # MySQL DATETIME 預設只保存整秒，向上取整才能保證至少完整安全期。
    return deadline.replace(microsecond=0) + timedelta(seconds=bool(deadline.microsecond))


def _scope():
    bucket = getattr(settings, "GCS_IMAGE_BUCKET", "")
    environment = getattr(settings, "APP_ENV", "")
    if (not getattr(settings, "IMAGE_STORAGE_ENABLED", False)
            or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket)
            or not re.fullmatch(r"[a-z0-9_-]{1,30}", environment)):
        raise HTTPException(status_code=503, detail="圖片儲存尚未設定獨立環境與 bucket")
    return bucket, environment, f"coffeehub-managed/{environment}/"


def normalize_image(contents, declared_type):
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="單張圖片不得超過 5 MiB")
    try:
        with Image.open(BytesIO(contents), formats=list(FORMATS)) as image:
            image_format = image.format
            mime, extension = FORMATS[image_format]
            if declared_type != mime:
                raise HTTPException(status_code=415, detail="宣告格式與圖片實際內容不一致")
            width, height = image.size
            if (max(width, height) > min(8192, getattr(settings, "IMAGE_MAX_DIMENSION", 8192))
                    or width * height > min(20_000_000, getattr(settings, "IMAGE_MAX_PIXELS", 20_000_000))):
                raise HTTPException(status_code=413, detail="圖片像素超過允許上限")
            if getattr(image, "n_frames", 1) != 1 or getattr(image, "is_animated", False):
                raise HTTPException(status_code=415, detail="不支援動畫或多頁圖片")
            image.verify()
        with Image.open(BytesIO(contents), formats=list(FORMATS)) as image:
            image.load()
            rotated = ImageOps.exif_transpose(image)
            mode = "RGB" if image_format == "JPEG" else "RGBA"
            converted = rotated.convert(mode)
            # 從像素建立全新影像，避免 EXIF／XMP／註解等非必要資料隨 copy 留下。
            clean = Image.frombytes(mode, converted.size, converted.tobytes())
            output = BytesIO()
            clean.save(output, format=image_format)
            normalized = output.getvalue()
            if len(normalized) > MAX_BYTES:
                raise HTTPException(status_code=413, detail="清理後圖片超過 5 MiB")
            return normalized, mime, extension, clean.width, clean.height
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        raise HTTPException(status_code=415, detail="圖片內容損毀或不是支援的格式")


def image_urls(product):
    return set(([product.main_image] if product.main_image else []) + (product.sub_images or []))


async def _audit(db, request, actor_id, action, product_id, before=None, after=None, status="SUCCESS"):
    await record_required_action(db, request, user_id=actor_id, category="IMAGE", target_type="PRODUCT",
        action=action, target_id=product_id, before_data=before, after_data=after, status=status)


async def synchronize_product_images(db, request, actor, product, before_urls, before_layout=None):
    urls = ([product.main_image] if product.main_image else []) + (product.sub_images or [])
    if len(product.sub_images or []) > 3 or len(urls) != len(set(urls)):
        raise HTTPException(status_code=422, detail="最多 1 張主圖及 3 張不重複副圖")
    after_urls = set(urls)
    after_layout = [product.main_image, product.sub_images or []]
    if before_urls == after_urls and before_layout == after_layout:
        return
    # 所有關聯與清理以圖片列鎖序列化。舊未登記 URL 只能留在原商品，不自動刪除。
    assets = (await db.execute(select(ImageAsset).where(ImageAsset.public_url.in_(before_urls | after_urls))
        .order_by(ImageAsset.image_id).with_for_update().execution_options(populate_existing=True))).scalars().all()
    by_url = {asset.public_url: asset for asset in assets}
    for url in after_urls - before_urls:
        asset = by_url.get(url)
        if not asset or asset.product_id != product.product_id or asset.state != "ready":
            raise HTTPException(status_code=403, detail="只能關聯本商品已完成驗證上傳的圖片")
    added, removed = [], []
    for asset in assets:
        if asset.public_url in after_urls:
            if asset.state != "ready":
                raise HTTPException(status_code=409, detail="圖片尚未完成上傳或已進入清理")
            asset.cleanup_after = None
            asset.last_error = None
            added.append(asset.image_id)
        elif asset.public_url in before_urls:
            asset.cleanup_after = _after(_grace())
            removed.append(asset.image_id)
    await _audit(db, request, actor.user_id, "IMAGE_ASSOCIATE", product.product_id,
        before={"count": len(before_urls), "layout_hash": hashlib.sha256(json.dumps(before_layout).encode()).hexdigest()},
        after={"count": len(after_urls), "layout_hash": hashlib.sha256(json.dumps(after_layout).encode()).hexdigest(),
               "image_ids": added, "cleanup_candidates": removed})


async def upload_product_image(db, request, actor, product_id, contents, declared_type):
    from app.services.product_service import _locked_product
    bucket, environment, prefix = _scope()
    # 在解碼及雲端操作之前檢查商品所有權。
    try:
        await _locked_product(db, request, actor, product_id)
        normalized, mime, extension, width, height = await run_in_threadpool(normalize_image, contents, declared_type)
        image_id = str(uuid4())
        object_name = f"{prefix}{product_id}/{image_id}.{extension}"
        asset = ImageAsset(image_id=image_id, product_id=product_id, uploaded_by=actor.user_id,
            environment=environment, bucket=bucket, object_name=object_name,
            public_url=f"https://storage.googleapis.com/{bucket}/{object_name}",
            content_sha256=hashlib.sha256(normalized).hexdigest(), content_type=mime,
            size_bytes=len(normalized), width=width, height=height, cleanup_after=_after(_grace()))
        db.add(asset)
        await _audit(db, request, actor.user_id, "IMAGE_UPLOAD_INTENT", product_id,
            after={"image_id": image_id, "size_bytes": len(normalized)})
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="無法保存上傳意圖，未上傳圖片")
    # 意圖先提交。即使遠端成功但回應／DB 失敗，仍有可追蹤的延遲清理候選。
    try:
        generation = await run_in_threadpool(gcs_storage.upload_bytes, bucket, object_name,
            normalized, mime, image_id, asset.content_sha256)
        await _locked_product(db, request, actor, product_id)
        asset = (await db.execute(select(ImageAsset).where(ImageAsset.image_id == image_id)
            .with_for_update().execution_options(populate_existing=True))).scalar_one()
        if asset.state != "uploading":
            raise HTTPException(status_code=409, detail="上傳已進入其他處理狀態")
        asset.generation = int(generation)
        asset.state = "ready"
        await _audit(db, request, actor.user_id, "IMAGE_UPLOAD_READY", product_id,
            after={"image_id": image_id})
        response = {"message": "圖片已上傳，儲存商品後才完成關聯", "image_url": asset.public_url,
                    "filename": f"{image_id}.{extension}", "image_id": image_id}
        await db.commit()
        return response
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=502, detail="上傳未完成；原圖片未變更，新物件已登記為延遲清理候選")


async def process_image_cleanup(db, request, actor, dry_run=True, limit=10):
    from app.services.product_service import _locked_product
    if actor.role_id != 1:
        raise HTTPException(status_code=403, detail="僅 Admin 可執行圖片清理")
    # rollback 會使 ORM 欄位過期；後續每筆仍由 _locked_product 重查帳號及版本。
    actor = SimpleNamespace(user_id=actor.user_id, role_id=actor.role_id)
    bucket, environment, prefix = _scope()
    if not dry_run and not getattr(settings, "IMAGE_DELETE_ENABLED", False):
        raise HTTPException(status_code=403, detail="實際圖片刪除預設關閉")
    ids = (await db.execute(select(ImageAsset.image_id).where(ImageAsset.bucket == bucket,
        ImageAsset.environment == environment, ImageAsset.cleanup_after <= _now(),
        ImageAsset.state.in_(["uploading", "ready", "deleting"]), ImageAsset.is_held.is_(False))
        .order_by(ImageAsset.cleanup_after, ImageAsset.image_id).limit(limit))).scalars().all()
    # 清除前置查詢的快照；後續逐筆重新授權與鎖定。
    await db.rollback()
    result = {"dry_run": dry_run, "candidates": len(ids), "deleted": 0, "skipped": 0, "failed": 0}
    actor_id = actor.user_id
    for image_id in ids:
        asset = None
        intent_saved = False
        try:
            product_id = (await db.execute(select(ImageAsset.product_id).where(ImageAsset.image_id == image_id))).scalar_one()
            await _locked_product(db, request, actor, product_id)
            asset = (await db.execute(select(ImageAsset).where(ImageAsset.image_id == image_id)
                .with_for_update().execution_options(populate_existing=True))).scalar_one()
            if (asset.is_held or asset.cleanup_after is None or asset.cleanup_after > _now()
                    or asset.state not in ("uploading", "ready", "deleting")
                    or asset.bucket != bucket or asset.environment != environment
                    or not asset.object_name.startswith(prefix + str(asset.product_id) + "/")):
                result["skipped"] += 1
                await db.rollback()
                continue
            # current read，包括下架商品；不可僅依候選標記判斷引用。
            references = (await db.execute(select(Products.product_id)
                .where(or_(Products.main_image == asset.public_url,
                    func.json_contains(Products.sub_images, json.dumps(asset.public_url)) == 1))
                .order_by(Products.product_id).with_for_update())).scalars().all()
            if references:
                if dry_run:
                    result["skipped"] += 1
                    await db.rollback()
                    continue
                asset.state = "ready" if asset.state != "uploading" else asset.state
                asset.cleanup_after = None
                await _audit(db, request, actor_id, "IMAGE_CLEANUP_REFERENCED", product_id,
                    after={"image_id": image_id})
                await db.commit()
                result["skipped"] += 1
                continue
            if dry_run:
                await db.rollback()
                continue
            asset.state = "deleting"
            asset.cleanup_attempts += 1
            asset.cleanup_after = _after(_retry())
            asset.last_error = None
            expected_generation, expected_hash = asset.generation, asset.content_sha256
            object_name = asset.object_name
            await _audit(db, request, actor_id, "IMAGE_DELETE_INTENT", product_id, after={"image_id": image_id})
            await db.commit()
            intent_saved = True
            remote = await run_in_threadpool(gcs_storage.inspect_object, bucket, object_name)
            if remote:
                if (remote["held"] or remote["metadata"].get("coffeehub_image_id") != image_id
                        or remote["metadata"].get("sha256") != expected_hash
                        or (expected_generation is not None and remote["generation"] != expected_generation)):
                    raise ValueError("REMOTE_HOLD_OR_IDENTITY_MISMATCH")
                await run_in_threadpool(gcs_storage.delete_generation, bucket, object_name, remote["generation"])
            # 遠端刪除成功但本次 DB 失敗時，deleting 意圖仍保存，重試可由 NotFound 完成。
            await _locked_product(db, request, actor, product_id)
            asset = (await db.execute(select(ImageAsset).where(ImageAsset.image_id == image_id)
                .with_for_update().execution_options(populate_existing=True))).scalar_one()
            asset.state = "deleted"
            asset.cleanup_after = None
            asset.last_error = None
            await _audit(db, request, actor_id, "IMAGE_DELETE_COMPLETE", product_id, after={"image_id": image_id})
            await db.commit()
            result["deleted"] += 1
        except HTTPException:
            await db.rollback()
            raise
        except Exception as exc:
            await db.rollback()
            result["failed"] += 1
            logging.getLogger(__name__).warning("Image cleanup retry required (%s)", type(exc).__name__)
            # 意圖已持久保存；只記錄固定錯誤碼，不輸出 GCS 憑證／例外細節。
            try:
                asset = (await db.execute(select(ImageAsset).where(ImageAsset.image_id == image_id)
                    .with_for_update().execution_options(populate_existing=True))).scalar_one()
                asset.last_error = "CLEANUP_RETRY_REQUIRED"
                asset.cleanup_after = _after(_retry())
                if not intent_saved:
                    asset.cleanup_attempts += 1
                await _audit(db, request, actor_id, "IMAGE_DELETE_RETRY", asset.product_id,
                    after={"image_id": image_id}, status="FAILED")
                await db.commit()
            except Exception as retry_exc:
                await db.rollback()
                logging.getLogger(__name__).error("Image cleanup retry persistence failed (%s)", type(retry_exc).__name__)
    return result
