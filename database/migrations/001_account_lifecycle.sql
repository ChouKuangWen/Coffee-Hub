-- Batch 2 / DEC-015,017~023. 先備份並在隔離環境驗證，再由部署人員套用。
-- 既有資料庫增量遷移，不執行 init.sql，不重建或刪除任何業務資料。
-- MySQL DDL 會自動提交；請單一部署程序依序執行，不使用 mysql --force。
-- 每步檢查存在性，支援已完成或部分完成後重跑；僅全部成功才記錄版本。
-- 完成後才部署 Batch 2；舊格式 JWT 不再接受，所有使用者須重新登入。
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(100) PRIMARY KEY,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @coffeehub_m001_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema=DATABASE() AND table_name='users' AND column_name='is_active'),
    'DO 0', 'ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE');
PREPARE coffeehub_m001_stmt FROM @coffeehub_m001_sql;
EXECUTE coffeehub_m001_stmt;
DEALLOCATE PREPARE coffeehub_m001_stmt;

SET @coffeehub_m001_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema=DATABASE() AND table_name='users' AND column_name='token_version'),
    'DO 0', 'ALTER TABLE users ADD COLUMN token_version INT NOT NULL DEFAULT 0');
PREPARE coffeehub_m001_stmt FROM @coffeehub_m001_sql;
EXECUTE coffeehub_m001_stmt;
DEALLOCATE PREPARE coffeehub_m001_stmt;

CREATE TABLE IF NOT EXISTS seller_applications (
    application_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT NULL,
    reviewed_at DATETIME NULL,
    INDEX idx_seller_application_user (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO schema_migrations(version) VALUES ('001_account_lifecycle');
