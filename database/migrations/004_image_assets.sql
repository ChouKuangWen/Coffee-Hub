-- Batch 5：先套用 001～003；暫停圖片寫入，單一部署程序執行。
-- 不讀取 GCS、不回填或刪除舊物件；未登記的既有 URL 保留且不自動清理。
-- 清理：至少 7 天緩衝、失敗至少 24 小時後重試；實際刪除預設關閉。
-- 部署另設 IMAGE_STORAGE_ENABLED 與 GCS_IMAGE_BUCKET；依 APP_ENV 隔離物件前綴。
-- 清理由 Admin /upload/cleanup 呼叫，預設 dry_run；不自動啟用排程或 GCS 刪除。
-- 每步支援重跑；成功建立後才記錄版本。既有資料庫不得執行 init.sql。
CREATE TABLE IF NOT EXISTS image_assets (
    image_id VARCHAR(36) NOT NULL PRIMARY KEY,
    product_id INT NOT NULL,
    uploaded_by INT NOT NULL,
    environment VARCHAR(30) NOT NULL,
    bucket VARCHAR(63) NOT NULL,
    object_name VARCHAR(255) NOT NULL,
    public_url VARCHAR(512) NOT NULL UNIQUE,
    content_sha256 VARCHAR(64) NOT NULL,
    generation BIGINT NULL,
    content_type VARCHAR(20) NOT NULL,
    size_bytes INT NOT NULL,
    width INT NOT NULL,
    height INT NOT NULL,
    state VARCHAR(20) NOT NULL DEFAULT 'uploading',
    cleanup_after DATETIME NULL,
    cleanup_attempts INT NOT NULL DEFAULT 0,
    last_error VARCHAR(50) NULL,
    is_held BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_image_assets_product_id(product_id),
    INDEX ix_image_assets_cleanup_after(cleanup_after),
    UNIQUE KEY uq_image_asset_object(bucket,object_name),
    FOREIGN KEY(product_id) REFERENCES products(product_id),
    FOREIGN KEY(uploaded_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO schema_migrations(version) VALUES ('004_image_assets');
