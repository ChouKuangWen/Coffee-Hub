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
    name VARCHAR(50) NOT NULL COMMENT '角色名稱'
)ENGINE=InnoDB DEFAULT CHARSET=utf8MB4 COMMENT='角色資料表';

-- 權限資料表
CREATE TABLE permissions(
    permission_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '權限 ID',
    name VARCHAR(100) NOT NULL COMMENT '權限名稱'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='權限資料表';

-- 角色權限關聯資料表（多對多關聯表)
CREATE TABLE roles_permissions(
    role_id INT NOT NULL COMMENT '角色 ID',
    permission_id INT NOT NULL COMMENT '權限 ID',
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
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
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
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
    INDEX idx_category (product_category),
    INDEX idx_active (is_active),
    INDEX idx_origin (continent, country),
    INDEX idx_sales (sales_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '商品資料表';


-- 建立訂單資料表
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單 ID',
    user_id INT  NULL COMMENT '下單會員 ID',
    status VARCHAR(50) NOT NULL DEFAULT '待付款' COMMENT '訂單狀態',
    total DECIMAL(10,2) NOT NULL COMMENT '總金額',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    status_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '狀態變動時間',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='訂單資料表';

-- 建立訂單項目資料表
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單項目 ID',
    order_id INT NOT NULL COMMENT '訂單 ID',
    product_id INT  NULL COMMENT '商品 ID',
    user_id INT NULL COMMENT '使用者 ID',
    quantity INT NOT NULL COMMENT '數量',
    price DECIMAL(10,2) NOT NULL COMMENT '單價',
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='訂單項目資料表';

CREATE TABLE jwt_blacklist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jti VARCHAR(36) NOT NULL UNIQUE COMMENT 'JWT 的 jti 值',
    expires_at DATETIME NOT NULL COMMENT '該 JWT 的過期時間',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='jti黑名單資料表';

CREATE TABLE used_jwts (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自動遞增 ID',
    jti VARCHAR(255) NOT NULL UNIQUE COMMENT 'JWT 的唯一識別碼',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入黑名單的時間'
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='儲存已登出或作廢的 JWT ID';

CREATE TABLE refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    token TEXT NOT NULL,
    jti VARCHAR(255) NOT NULL,
    issued_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    INDEX (user_id),
    INDEX (jti)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='儲存使用者的 Refresh Token ';

-- 建立購物車項目資料表
CREATE TABLE cart_items (
    cart_item_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '購物車項目 ID',
    user_id INT NOT NULL COMMENT '使用者 ID',
    product_id INT NOT NULL COMMENT '商品 ID',
    quantity INT NOT NULL DEFAULT 1 COMMENT '購買數量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入時間',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_product (user_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='購物車資料表';

-- 建立RAG對話紀錄表
CREATE TABLE chat_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訊息 ID',
    user_id INT NOT NULL COMMENT '對應的使用者 ID',
    role ENUM('user', 'model') NOT NULL COMMENT '發言者：user(使用者) 或 model(AI)',
    content TEXT NOT NULL COMMENT '對話內容文字',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '發送時間',
    -- 外鍵關聯到 users 表，當使用者刪除時，對話紀錄隨之刪除
    CONSTRAINT fk_chat_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    -- 索引優化：讓查詢使用者的對話變得快
    INDEX idx_user_history (user_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RAG 聊天紀錄表';