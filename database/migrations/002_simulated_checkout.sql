-- Batch 3：先套用 001_account_lifecycle，再於單一部署程序執行本遷移。
-- 不刪除既有資料；DDL 自動提交，不使用 --force；各步存在性檢查支援重跑。
-- 舊明細名稱與賣家無可信成交時點資料，保持 NULL，不以現值冒充歷史快照。
-- 模擬建單僅在隔離測試環境設定 APP_ENV=test 且 ENABLE_SIMULATED_CHECKOUT=true。
SET @coffeehub_m002_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE()
            AND table_name='orders' AND column_name='checkout_key'),
    'DO 0', 'ALTER TABLE orders ADD COLUMN checkout_key VARCHAR(36) NULL');
PREPARE coffeehub_m002_stmt FROM @coffeehub_m002_sql;
EXECUTE coffeehub_m002_stmt;
DEALLOCATE PREPARE coffeehub_m002_stmt;

SET @coffeehub_m002_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE()
            AND table_name='orders' AND column_name='checkout_fingerprint'),
    'DO 0', 'ALTER TABLE orders ADD COLUMN checkout_fingerprint VARCHAR(64) NULL');
PREPARE coffeehub_m002_stmt FROM @coffeehub_m002_sql;
EXECUTE coffeehub_m002_stmt;
DEALLOCATE PREPARE coffeehub_m002_stmt;

SET @coffeehub_m002_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE()
            AND table_name='order_items' AND column_name='product_name'),
    'DO 0', 'ALTER TABLE order_items ADD COLUMN product_name VARCHAR(100) NULL');
PREPARE coffeehub_m002_stmt FROM @coffeehub_m002_sql;
EXECUTE coffeehub_m002_stmt;
DEALLOCATE PREPARE coffeehub_m002_stmt;

SET @coffeehub_m002_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE()
            AND table_name='order_items' AND column_name='seller_id'),
    'DO 0', 'ALTER TABLE order_items ADD COLUMN seller_id INT NULL');
PREPARE coffeehub_m002_stmt FROM @coffeehub_m002_sql;
EXECUTE coffeehub_m002_stmt;
DEALLOCATE PREPARE coffeehub_m002_stmt;

SET @coffeehub_m002_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='orders' AND index_name='uq_orders_checkout'),
    'DO 0', 'ALTER TABLE orders ADD UNIQUE KEY uq_orders_checkout(user_id,checkout_key)');
PREPARE coffeehub_m002_stmt FROM @coffeehub_m002_sql;
EXECUTE coffeehub_m002_stmt;
DEALLOCATE PREPARE coffeehub_m002_stmt;

SET @coffeehub_m002_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.key_column_usage WHERE table_schema=DATABASE()
            AND table_name='order_items' AND column_name='seller_id' AND referenced_table_name='users'),
    'DO 0', 'ALTER TABLE order_items ADD CONSTRAINT fk_oi_snapshot_seller FOREIGN KEY(seller_id) REFERENCES users(user_id)');
PREPARE coffeehub_m002_stmt FROM @coffeehub_m002_sql;
EXECUTE coffeehub_m002_stmt;
DEALLOCATE PREPARE coffeehub_m002_stmt;

INSERT IGNORE INTO schema_migrations(version) VALUES ('002_simulated_checkout');
