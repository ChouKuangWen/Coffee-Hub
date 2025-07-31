-- 建立資料庫
CREATE DATABASE `member_order_management_backend_system`
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
    price DECIMAL(10,2) NOT NULL COMMENT '價格',
    stock INT NOT NULL COMMENT '庫存',
    description TEXT DEFAULT NULL COMMENT '描述'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '商品資料表';


-- 建立訂單資料表
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單 ID',
    user_id INT NOT NULL COMMENT '下單會員 ID',
    status VARCHAR(50) NOT NULL DEFAULT '待付款' COMMENT '訂單狀態',
    total DECIMAL(10,2) NOT NULL COMMENT '總金額',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    status_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '狀態變動時間',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='訂單資料表';

-- 建立訂單項目資料表
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單項目 ID',
    order_id INT NOT NULL COMMENT '訂單 ID',
    product_id INT NOT NULL COMMENT '商品 ID',
    quantity INT NOT NULL COMMENT '數量',
    price DECIMAL(10,2) NOT NULL COMMENT '單價',
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
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