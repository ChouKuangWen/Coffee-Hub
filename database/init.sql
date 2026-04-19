SET NAMES 'utf8mb4';
SET character_set_client = utf8mb4;

DROP DATABASE IF EXISTS `member_order_management_backend_system`;
-- 建立資料庫
CREATE DATABASE IF NOT EXISTS `member_order_management_backend_system`
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

-- 切換到目標資料庫
USE member_order_management_backend_system;

-- 角色資料表
CREATE TABLE roles(
    role_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色 ID',
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名稱'
)ENGINE=InnoDB DEFAULT CHARSET=utf8MB4 COMMENT='角色資料表';

-- 權限資料表
CREATE TABLE permissions(
    permission_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '權限 ID',
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '權限名稱'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='權限資料表';

-- 角色權限關聯資料表（多對多關聯表)
CREATE TABLE roles_permissions(
    role_id INT NOT NULL COMMENT '角色 ID',
    permission_id INT NOT NULL COMMENT '權限 ID',
    PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '角色權限關聯表';

--  建立使用者資料表
CREATE TABLE users(
    user_id INT AUTO_INCREMENT PRIMARY KEY COMMENT'使用者 ID',
    username VARCHAR(50) NOT NULL COMMENT '帳號名稱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密碼 hash',
    email VARCHAR(100) NOT NULL COMMENT '信箱',
    phone VARCHAR(20) NOT NULL COMMENT '電話',
    address VARCHAR(255) NOT NULL COMMENT '地址',
    role_id INT NOT NULL COMMENT '角色 ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP  COMMENT '建立時間',
    UNIQUE KEY unique_username(username),
    UNIQUE KEY unique_email(email),
    -- 新增效能索引 (針對 JOIN 與 排序)
    INDEX idx_user_role_id (role_id) COMMENT '加速角色關聯查詢',
    INDEX idx_user_created_at (created_at) COMMENT '加速註冊時間排序',

    -- 外鍵約束 (建議明確命名，方便未來維護)
    CONSTRAINT fk_users_role_id FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='會員資料表';

-- 建立產品資料表
CREATE TABLE products(
    product_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '商品ID',
    name VARCHAR(100) NOT NULL COMMENT '商品名稱',
    main_image VARCHAR(512) DEFAULT NULL COMMENT '主圖 URL',
    sub_images JSON DEFAULT NULL COMMENT '副圖 URL 清單 (JSON 陣列)',
    price DECIMAL(10,2) NOT NULL COMMENT '價格',
    stock INT NOT NULL DEFAULT 0 COMMENT '庫存',
    sales_count INT NOT NULL DEFAULT 0 COMMENT '總銷售量',
    product_category ENUM('green_bean', 'roasted_bean') NOT NULL DEFAULT 'roasted_bean' COMMENT '類別 (生豆/熟豆)',
    continent VARCHAR(20) DEFAULT NULL COMMENT '洲別',
    country VARCHAR(100) DEFAULT NULL COMMENT '國家',
    region VARCHAR(100) DEFAULT NULL COMMENT '產區',
    process_method VARCHAR(50) DEFAULT NULL COMMENT '處理法',
    roast_level VARCHAR(50) DEFAULT NULL COMMENT '烘焙度 (生豆為建議度/熟豆為實際度)',
    variety VARCHAR(100) DEFAULT NULL COMMENT '品種',
    grade_size VARCHAR(50) DEFAULT NULL COMMENT '等級/大小',
    harvest_year VARCHAR(20) DEFAULT NULL COMMENT '採收年份',
    altitude VARCHAR(50) DEFAULT NULL COMMENT '海拔',
    moisture_content DECIMAL(4,2) DEFAULT NULL COMMENT '含水量 (%)',
    density INT DEFAULT NULL COMMENT '密度 (g/l)',
    flavor_tags VARCHAR(255) DEFAULT NULL COMMENT '風味標籤',
    description TEXT DEFAULT NULL COMMENT '詳細描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '上架狀態',
    owner_id INT NOT NULL COMMENT '商品擁有者 (賣家)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE,
    -- 索引優化清單
    INDEX idx_owner_id (owner_id),          -- 補強：查詢賣家商品
    INDEX idx_price (price),                -- 補強：價格過濾/排序
    INDEX idx_category (product_category),
    INDEX idx_active (is_active),
    INDEX idx_origin (continent, country),  -- 複合索引：產地篩選
    INDEX idx_sales (sales_count),          -- 排序：熱銷排行
    INDEX idx_created_at (created_at),      -- 排序：新品上市
    CONSTRAINT fk_products_owner FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '商品資料表';


-- 建立訂單資料表
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單 ID',
    user_id INT  NULL COMMENT '下單會員 ID',
    status VARCHAR(50) NOT NULL DEFAULT '待付款' COMMENT '訂單狀態',
    total DECIMAL(10,2) NOT NULL COMMENT '總金額',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    status_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '狀態變動時間',
    -- 索引優化清單
    INDEX idx_order_user_id (user_id),          -- 查詢用戶訂單
    INDEX idx_order_status (status),            -- 狀態篩選 (待付款/已出貨)
    INDEX idx_order_created_at (created_at),    -- 日期排序
    CONSTRAINT fk_orders_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='訂單資料表';

-- 建立訂單項目資料表
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單項目 ID',
    order_id INT NOT NULL COMMENT '訂單 ID',
    product_id INT  NULL COMMENT '商品 ID',
    quantity INT NOT NULL COMMENT '數量',
    price DECIMAL(10,2) NOT NULL COMMENT '單價',
    -- 索引優化
    INDEX idx_oi_order_id (order_id),
    INDEX idx_oi_product_id (product_id),
    CONSTRAINT fk_oi_order_id FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_oi_product_id FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='訂單項目資料表';

CREATE TABLE jwt_blacklist (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自動遞增 ID',
    jti VARCHAR(255) NOT NULL UNIQUE COMMENT 'WT 的唯一識別碼',
    expires_at DATETIME NOT NULL COMMENT '該 JWT 的過期時間',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入黑名單的時間',
    INDEX idx_blacklist_jti (jti)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='儲存已登出或作廢的 JWT ID';

CREATE TABLE refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自動遞增 ID',
    user_id INT NOT NULL COMMENT '使用者 ID',
    token TEXT NOT NULL COMMENT '長效 Token 內容',
    jti VARCHAR(255) NOT NULL UNIQUE COMMENT 'Refresh Token 的唯一識別碼',
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    -- 索引優化：加速根據使用者或狀態進行查詢
    INDEX idx_rt_user (user_id),
    INDEX idx_rt_jti (jti),
    INDEX idx_rt_status (is_revoked, expires_at),
    -- 外鍵約束：當使用者被刪除時，自動清理其所有 Token
    CONSTRAINT fk_rt_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Refresh Token 管理表';

-- 建立購物車項目資料表
CREATE TABLE cart_items (
    cart_item_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '購物車項目 ID',
    user_id INT NOT NULL COMMENT '使用者 ID',
    product_id INT NOT NULL COMMENT '商品 ID',
    quantity INT NOT NULL DEFAULT 1 COMMENT '購買數量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入時間',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
    -- 索引優化
    INDEX idx_cart_user_id (user_id), -- 加速讀取個人購物車
    INDEX idx_cart_updated_at (updated_at), -- 讓最新加入的商品排在最前面
    -- 約束
    CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_product (user_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='購物車資料表';

-- 建立RAG對話紀錄表
CREATE TABLE chat_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訊息 ID',
    user_id INT NOT NULL COMMENT '對應的使用者 ID',
    role ENUM('user', 'model') NOT NULL COMMENT '發言者：user(使用者) 或 model(AI)',
    content TEXT NOT NULL COMMENT '對話內容文字',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '發送時間',
    -- 索引優化：加速對話歷史讀取
    INDEX idx_user_history (user_id, created_at DESC),
    INDEX idx_chat_created (created_at),

    -- 外鍵關聯
    CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RAG 聊天紀錄表';

-- 建立Log紀錄表
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    `user_id` INT NULL COMMENT '執行操作的使用者ID（系統操作可為 NULL）',
    
    `category` VARCHAR(50) NOT NULL COMMENT '類別：ORDER / PRODUCT / USER / AUTH / SYSTEM',
    `action` VARCHAR(100) NOT NULL COMMENT '具體動作：CREATE / UPDATE / DELETE / LOGIN',
    
    `target_type` VARCHAR(50) DEFAULT NULL COMMENT '操作對象類型：ORDER / PRODUCT / USER',
    `target_id` VARCHAR(100) DEFAULT NULL COMMENT '受影響的對象ID',
    
    `status` VARCHAR(20) NOT NULL DEFAULT 'SUCCESS' COMMENT 'SUCCESS / FAIL',
    `error_message` TEXT DEFAULT NULL COMMENT '錯誤訊息（失敗時使用）',
    
    `before_data` JSON DEFAULT NULL COMMENT '變更前資料',
    `after_data` JSON DEFAULT NULL COMMENT '變更後資料',
    
    `request_id` VARCHAR(100) DEFAULT NULL COMMENT '請求追蹤ID',
    
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `user_agent` TEXT DEFAULT NULL,
    
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_category_action` (`category`, `action`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_target` (`target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;