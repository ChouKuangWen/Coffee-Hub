-- Batch 4：依序套用 001、002、003；單一部署程序執行，不使用 --force。
-- DDL 自動提交；存在性檢查支援部分完成後重跑，不刪除既有業務資料。
-- 升級期間暫停模擬建單／狀態寫入；003 全部成功後才部署 Batch 4。
-- 使用者確認的規則：各 Seller 只出貨本人品項，全部出貨才彙總整單已出貨。
-- 任一品項出貨後，不接受一般整單取消申請／核准。
SET @coffeehub_m003_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE()
            AND table_name='orders' AND column_name='stock_deducted'),
    'DO 0', 'ALTER TABLE orders ADD COLUMN stock_deducted BOOLEAN NOT NULL DEFAULT FALSE');
PREPARE coffeehub_m003_stmt FROM @coffeehub_m003_sql;
EXECUTE coffeehub_m003_stmt;
DEALLOCATE PREPARE coffeehub_m003_stmt;

SET @coffeehub_m003_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE()
            AND table_name='orders' AND column_name='stock_returned_at'),
    'DO 0', 'ALTER TABLE orders ADD COLUMN stock_returned_at DATETIME NULL');
PREPARE coffeehub_m003_stmt FROM @coffeehub_m003_sql;
EXECUTE coffeehub_m003_stmt;
DEALLOCATE PREPARE coffeehub_m003_stmt;

SET @coffeehub_m003_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE()
            AND table_name='order_items' AND column_name='shipped_at'),
    'DO 0', 'ALTER TABLE order_items ADD COLUMN shipped_at DATETIME NULL');
PREPARE coffeehub_m003_stmt FROM @coffeehub_m003_sql;
EXECUTE coffeehub_m003_stmt;
DEALLOCATE PREPARE coffeehub_m003_stmt;

CREATE TABLE IF NOT EXISTS order_cancellations (
    cancellation_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    requested_by INT NOT NULL,
    reason VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT NULL,
    reviewed_at DATETIME NULL,
    review_note VARCHAR(500) NULL,
    INDEX ix_order_cancellations_order_id(order_id),
    FOREIGN KEY(order_id) REFERENCES orders(order_id),
    FOREIGN KEY(requested_by) REFERENCES users(user_id),
    FOREIGN KEY(reviewed_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 僅首次升級識別 Batch 3 的完整可信轉單，不以現價／現名回填舊快照。
-- Batch 3 不提供出貨／取消，故不回填 shipped_at 或 stock_returned_at。
UPDATE orders o SET o.stock_deducted=TRUE
WHERE o.stock_deducted=FALSE AND o.stock_returned_at IS NULL
  AND o.checkout_key IS NOT NULL AND o.checkout_fingerprint IS NOT NULL
  AND o.status IN ('待付款','已付款','待出貨')
  AND NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version='003_order_lifecycle')
  AND EXISTS (SELECT 1 FROM audit_logs a WHERE a.category='ORDER' AND a.action='SIMULATED_CREATE'
              AND a.target_type='ORDER' AND a.target_id=CAST(o.order_id AS CHAR) AND a.status='SUCCESS')
  AND EXISTS (SELECT 1 FROM order_items i WHERE i.order_id=o.order_id)
  AND NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id=o.order_id
                  AND (i.product_id IS NULL OR i.product_name IS NULL OR i.seller_id IS NULL
                       OR i.quantity<=0 OR i.price<=0))
  AND o.total=(SELECT SUM(i.quantity*i.price) FROM order_items i WHERE i.order_id=o.order_id);

INSERT IGNORE INTO schema_migrations(version) VALUES ('003_order_lifecycle');
