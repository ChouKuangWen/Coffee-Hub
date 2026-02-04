SET NAMES 'utf8mb4';
SET character_set_client = utf8mb4;
USE member_order_management_backend_system;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE roles_permissions;
TRUNCATE TABLE permissions;
TRUNCATE TABLE roles;
TRUNCATE TABLE users;
TRUNCATE TABLE products;
TRUNCATE TABLE order_items;
TRUNCATE TABLE orders;
SET FOREIGN_KEY_CHECKS = 1;


-- 2. 角色與權限 (ID: 1 Admin, 2 Seller, 3 Customer)
INSERT INTO roles (role_id, name) VALUES 
(1, 'Admin'), 
(2, 'Seller'), 
(3, 'Customer');

INSERT INTO permissions (permission_id, name) VALUES 
(1,'View Users'), 
(2,'Edit Users'), 
(3,'View Orders'), 
(4,'Edit Orders'), 
(5,'View Products'), 
(6,'Edit Products');

INSERT INTO roles_permissions (role_id, permission_id) VALUES 
(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),
(2,3),(2,5),(2,6),
(3,3),(3,5);

-- 3. 用戶資料 (ID 1-30)
-- 管理員 (role_id = 1): user1, user2
-- 賣家 (role_id = 2): user3 - user10
-- 買家 (role_id = 3): user11 - user30

INSERT INTO users (user_id, username, password_hash, email, phone, address, role_id) VALUES
(1, 'user1', '$2b$12$p9rSK2tnQFpo5c7sVtzOO.bkl.VL6Q/TkRa17MFkVBdy19FnRa3BC', 'user1@example.com', '0900000001', '台北總部', 1),
(2, 'user2', '$2b$12$co2RU/g0kI60mj6ElZXv2.SskpqeHfs89cVJESwoseXfknSeg/yD2', 'user2@example.com', '0911000002', '台中分部', 1),
(3, 'user3', '$2b$12$UubpWXdqoAOy74RU0nS.GuDUqA9pkYf8a3qEfQgzCc12Y5vPa8Er6', 'user3@example.com', '0922000003', '南投縣', 2),
(4, 'user4', '$2b$12$f0gkf.iQ/rvhfLpXHWweiO099pAW60ouBLunlQ68bddJYlO7107dW', 'user4@example.com', '0922000004', '雲林縣', 2),
(5, 'user5', '$2b$12$U5eGelWE/V1CjeR1uAG1su3VrlSd3iev0wXCPpDXpSJFm5TG6NhWa', 'user5@example.com', '0922000005', '高雄市', 2),
(6, 'user6', '$2b$12$r8NUbifaJezOsZqNwRE/NucdNKxFk4ZXnIuF9GxeWpYLkn5viIuV6', 'user6@example.com', '0922000006', '嘉義縣', 2),
(7, 'user7', '$2b$12$Ku58DcnDg9rUofGY/Y1M3u2gf9CTU2MjBxKnjxHOG1mym0J6ftuRa', 'user7@example.com', '0922000007', '宜蘭縣', 2),
(8, 'user8', '$2b$12$Cl31TleyhKZAR6PD4.a81etQSSiqUjUo1gI.wsvkVH0M212l2q/vO', 'user8@example.com', '0922000008', '桃園市', 2),
(9, 'user9', '$2b$12$5qyw.5y/hkfoOMDOk.SaCe.Nab3K6dDjyJVHoEEo8ntDfiFRDQMNu', 'user9@example.com', '0922000009', '新竹縣', 2),
(10, 'user10', '$2b$12$YFtbXq7RaKdAMz3JLnn6Xu8ddRxT0ZDEY2I04TtDMtfSPQab0GBK6', 'user10@example.com', '0922000010', '苗栗縣', 2),
(11, 'user11', '$2b$12$cqbjexH5d..qGbM9Ob8nB.NZIKALZrTnfxEYAehPunPxclNNII4iK', 'user11@example.com', '0900000011', '雲林縣', 3),
(12, 'user12', '$2b$12$2HNNplxR6uMrLQMQOWoNrOSnLaUY5OTSkQL26J2u5rZiNAjunqNM6', 'user12@example.com', '0900000012', '屏東縣', 3),
(13, 'user13', '$2b$12$D2f4fssUDs5kk/GFXA4A/unDbbzCdO.gaWRYHtu9Ty.LAhjEgFKC6', 'user13@example.com', '0900000013', '桃園市', 3),
(14, 'user14', '$2b$12$PmnWi2S0N1p0pvBBmKhsYutaXMgQMQeU9/HlW34FTVzMVl4rQ2Qvu', 'user14@example.com', '0900000014', '桃園市', 3),
(15, 'user15', '$2b$12$HYqXXE53am.b36vxOJ7AveTiyyvs/.tcKm7zFDEMmIP9W3JQZtabi', 'user15@example.com', '0900000015', '南投縣', 3),
(16, 'user16', '$2b$12$K9Aow0WLnvaz4.MIYNypVu5AUhhdY6uiFLTn9Z.AKTewhyrCWBgwW', 'user16@example.com', '0900000016', '宜蘭縣', 3),
(17, 'user17', '$2b$12$brYw1JJ0WKRWmpXeqTwVnOtdywRAvy0gxRjIrzB5UThP.PUs98F9C', 'user17@example.com', '0900000017', '花蓮縣', 3),
(18, 'user18', '$2b$12$LQ/JLRQoIk.56s/qamHnw.JIriVGZACMswu7WbilB.fz2SodPpXPO', 'user18@example.com', '0900000018', '台東縣', 3),
(19, 'user19', '$2b$12$Aa0Xbk/X3rEgmvSjeSzJDefg41IClsb6ZpsyHZmoB7.BXZ9xG9m5y', 'user19@example.com', '0900000019', '新北市', 3),
(20, 'user20', '$2b$12$O2lE7WnacyLX6siEJY/qv.wxST99R/Pn0GNTyt.m9DTfWwa3leOe.', 'user20@example.com', '0900000020', '台北市', 3),
(21, 'user21', '$2b$12$RLJ3qiSLdx.JlmPiw6F9h.j2rYfGi7Y2wyIuP8iP7/ItVGRshrCFK', 'user21@example.com', '0900000021', '台北市', 3),
(22, 'user22', '$2b$12$.SICy5RFduUL69BHGDQlE.0hJxIPPHr3UQeRtM9QuiPUXfgvOA5K2', 'user22@example.com', '0900000022', '南投縣', 3),
(23, 'user23', '$2b$12$UsfNV8hx6JDXR5w15boz5.0Vskht38oy7s5sQjPiQY6SsVigCxWY2', 'user23@example.com', '0900000023', '台北市', 3),
(24, 'user24', '$2b$12$cZMpdAxuDpy8GqUJVdFSreA7ez.fMiwfr5VbntObggIOgEDzTqnXe', 'user24@example.com', '0900000024', '台北市', 3),
(25, 'user25', '$2b$12$nnsYXK8HvtZppFQ5AKqt1urhtO6pLD17sMLR8KJtVfCfpO4TnrFIC', 'user25@example.com', '0900000025', '台北市', 3),
(26, 'user26', '$2b$12$mo6OeKfaRR3gTSX6d6wny.IJPxM7iNlxevjsZBO.5YNAMapGGolbm', 'user26@example.com', '0900000026', '台北市', 3),
(27, 'user27', '$2b$12$qXzj9.mji3V5M8nAT4dp9ueSMfPVpGawf99jRg8d0XSt7flfsIeM2', 'user27@example.com', '0900000027', '台新北市', 3),
(28, 'user28', '$2b$12$bTmF.VjeDUyqr33P.BCPFujlUvk8MJwljEQ9Xvby2RWKhDUxvFbyu', 'user28@example.com', '0900000028', '桃園市', 3),
(29, 'user29', '$2b$12$EvBb0hQD.xlvPT.0gCL5C.rx0lgXHzWRnc3vCkd67W8ZWzSfPKdie', 'user29@example.com', '0900000029', '新北市', 3),
(30, 'user30', '$2b$12$9ZCi4kHRuTPeCTTuU1funu.aEeyny4ZKQxQAC0Lg22DaebzshJ4j6', 'user30@example.com', '0900000030', '新北市', 3);

-- 此區為可以測試使用之帳號密碼：
-- user1 真實密碼:hashed_pwd1
-- user2 真實密碼:hashed_pwd2
-- user3 真實密碼:hashed_pwd3
-- user4 真實密碼:hashed_pwd4
-- user5 真實密碼:hashed_pwd5
-- user6 真實密碼:hashed_pwd6
-- user7 真實密碼:hashed_pwd7
-- user8 真實密碼:hashed_pwd8
-- user9 真實密碼:hashed_pwd9
-- user10 真實密碼:hashed_pwd10
-- user11 真實密碼:hashed_pwd11
-- user12 真實密碼:hashed_pwd12
-- user13 真實密碼:hashed_pwd13
-- user14 真實密碼:hashed_pwd14
-- user15 真實密碼:hashed_pwd15
-- user16 真實密碼:hashed_pwd16
-- user17 真實密碼:hashed_pwd17
-- user18 真實密碼:hashed_pwd18
-- user19 真實密碼:hashed_pwd19
-- user20 真實密碼:hashed_pwd20
-- user21 真實密碼:hashed_pwd21
-- user22 真實密碼:hashed_pwd22
-- user23 真實密碼:hashed_pwd23
-- user24 真實密碼:hashed_pwd24
-- user25 真實密碼:hashed_pwd25
-- user26 真實密碼:hashed_pwd26
-- user27 真實密碼:hashed_pwd27
-- user28 真實密碼:hashed_pwd28
-- user29 真實密碼:hashed_pwd29
-- user30 真實密碼:hashed_pwd30


-- 4. 產品資料 (20 筆 - 全中文化與 Model 對齊)
INSERT INTO products (
    product_id, name, main_image, sub_images, price, stock, sales_count, product_category, 
    continent, country, region, process_method, roast_level, variety, grade_size, 
    harvest_year, altitude, moisture_content, density, flavor_tags, description, is_active, owner_id, created_at, updated_at
) VALUES 
(1, '衣索比亞 耶加雪菲 G1', 'https://storage.googleapis.com/production-picture/%E8%A1%A3%E7%B4%A2%E6%AF%94%E4%BA%9E%20%E8%80%B6%E5%8A%A0%E9%9B%AA%E8%8F%B2%20G1.png', '[]', 450.00, 50, 10, 'roasted_bean', '非洲', '衣索比亞', '潔蒂普', '水洗', '淺焙', '原生種', 'G1', '2024', '2000m', 11.2, 710, '檸檬, 茉莉', '這是一款來自衣索比亞著名產區「潔蒂普 (Gedeb)」的頂級 G1 等級咖啡豆。\n採用傳統水洗處理法與淺焙工藝，極大化地保留了精品咖啡最純粹的花香與果酸。\n\n【口感特徵】\n● 入口：感受如新鮮檸檬般的明亮酸質，口感清爽且乾淨度極高。\n● 中段：伴隨著優雅的茉莉花香，層次豐富。\n● 餘韻：悠長且帶有淡淡的清新感，像是啜飲一杯優質花果茶。\n\n【感官平衡】\n● 酸度表現：優異且活潑\n● 苦度表現：極低\n● 酒體 (Body)：輕盈滑順\n\n【推薦對象】\n1. 喜歡清新、不苦、層次豐富手沖風味的消費者。\n2. 偏好高酸度調性或喜歡花草系風味的咖啡愛好者。\n3. 追求經典耶加雪菲「水洗乾淨感」的精品咖啡入門者。\n\n【建議沖煮水溫】：88°C - 91°C\n\n關鍵關鍵字：柑橘調、清爽、酸質活潑、花香調、夏日推薦。', 1, 3, NOW(), NOW()),
(2, '肯亞 AA 涅里', 'https://storage.googleapis.com/production-picture/%E8%82%AF%E4%BA%9E%20AA%20%E6%B6%85%E9%87%8C.png', '[]', 550.00, 30, 5, 'roasted_bean', '非洲', '肯亞', '尼耶利', '雙重水洗', '中淺焙', 'SL28, SL34', 'AA', '2024', '1700m', 10.5, 730, '烏梅, 黑醋栗', '這是一款來自肯亞著名產區「涅里 (Nyeri)」的頂級 AA 級咖啡豆。\n採用當地標準的「雙重水洗」處理法，造就了其極其乾淨且強烈飽滿的風味調性。\n\n【口感特徵】\n● 入口：強烈且豐富的黑醋栗與莓果酸香，層次分明。\n● 中段：帶有濃郁的烏梅甜感，伴隨著飽滿的果汁口感。\n● 餘韻：結尾帶有番茄與紅糖般的飽滿甜感，韻味扎實且多汁。\n\n【感官平衡】\n● 酸度表現：極高且具侵略性，果酸感強烈\n● 苦度表現：極低\n● 酒體 (Body)：扎實且濃厚 (Juicy)\n\n【推薦對象】\n1. 喜歡強烈、奔放、果酸感極其明顯的咖啡愛好者。\n2. 追求肯亞經典「烏梅調性」與紮實口感的消費者。\n3. 希望嘗試與耶加雪菲截然不同的、具備強勁酸質的精品咖啡玩家。\n\n【建議沖煮水溫】：88°C - 91°C\n\n關鍵關鍵字：莓果酸、烏梅調、強烈多汁、厚實感、深色水果風味。', 1, 3, NOW(), NOW()),
(3, '哥倫比亞 聖圖阿里歐', 'https://storage.googleapis.com/production-picture/%E5%93%A5%E5%80%AB%E6%AF%94%E4%BA%9E%20%E8%81%96%E5%9C%96%E9%98%BF%E9%87%8C%E6%AD%90.png', '[]', 420.00, 100, 2, 'green_bean', '南美洲', '哥倫比亞', '考卡省', '蜜處理', '無', '紅波旁', 'Excelso', '2023', '1550m', 11.0, 690, '甜橙, 巧克力', '這是一款來自哥倫比亞頂級莊園「聖圖阿里歐 (Santuario)」的精選豆。\n透過蜜處理法保留了較多果膠，使這款咖啡在酸與甜之間達到了極佳的平衡感。\n\n【口感特徵】\n● 入口：明顯的甜橙與柑橘酸香，酸質柔順且溫和。\n● 中段：展現出如焦糖般的甜感，伴隨著圓潤的口感。\n● 餘韻：尾韻帶有濃郁的黑巧克力香氣，甘甜回味，層次穩定。\n\n【感官平衡】\n● 酸度表現：中等且柔和，具備水果糖般的甜酸感\n● 苦度表現：極低，帶有些微可可風味\n● Body：圓潤且厚實，口感如絲綢般滑順\n\n【建議沖煮水溫】：88°C - 90°C\n\n【推薦對象】\n1. 怕酸也怕苦，追求咖啡中「酸甜平衡」與高度穩定性的消費者。\n2. 喜歡巧克力與焦糖後韻，但不希望咖啡太過濃厚沉重的愛好者。\n3. 適合尋找日常「全天候飲用」且不膩口的精品咖啡選擇。\n\n關鍵關鍵字：酸甜平衡、甜橙香氣、巧克力尾韻、圓潤口感、蜜處理甜感。', 1, 5, NOW(), NOW()),
(4, '黃金曼特寧', 'https://storage.googleapis.com/production-picture/%E9%BB%83%E9%87%91%E6%9B%BC%E7%89%B9%E5%AF%A7.png', '[]', 480.00, 40, 15, 'roasted_bean', '亞洲', '印尼', '蘇門答臘', '濕剝法', '中深焙', '鐵皮卡', 'TP G1', '2023', '1400m', 12.5, 680, '奶油, 藥草', '這是一款產自印尼蘇門答臘、採用獨特「濕剝法」處理的黃金曼特寧。中深焙度賦予了它極其厚實的 Body 與低酸度的特性。\n\n【口感特徵】\n● 入口：感受濃郁的奶油滑順感與沉穩的草本藥草香氣。\n● 中段：帶有獨特的森林泥土氣息與豐富的油脂感。\n● 餘韻：深邃且甜度持久，適合不愛果酸、追求濃厚口感的愛好者。\n\n【建議沖煮水溫】：88°C - 90°C\n\n關鍵字：厚實、低酸、藥草、奶油感', 1, 4, NOW(), NOW()),
(5, '巴西 喜拉朵', 'https://storage.googleapis.com/production-picture/%E5%B7%B4%E8%A5%BF%20%E5%96%9C%E6%8B%89%E6%9C%B5.png', '[]', 350.00, 150, 40, 'roasted_bean', '南美洲', '巴西', '喜拉朵', '日曬', '中焙', '阿拉比卡', 'NY2', '2023', '1100m', 11.5, 670, '堅果, 焦糖', '來自巴西喜拉朵產區，採用傳統日曬處理。這是一款經典的南美風味，以高度平衡與香甜口感著稱。\n\n【口感特徵】\n● 入口：散發迷人的烤堅果與花生香氣。\n● 中段：溫潤的焦糖甜感與巧克力基調，酸質極低且平易近人。\n● 餘韻：乾淨乾爽，非常適合作為每日飲用或搭配甜點。\n\n【建議沖煮水溫】：88°C - 91°C\n\n關鍵字：堅果、焦糖、平衡、適合大眾', 1, 6, NOW(), NOW()),
(6, '巴拿馬 波奎特 SHB', 'https://storage.googleapis.com/production-picture/%E5%B7%B4%E6%8B%BF%E9%A6%AC%20%E6%B3%A2%E5%A5%8E%E7%89%B9.png', '[]', 650.00, 20, 5, 'roasted_bean', '中美洲', '巴拿馬', '波奎特', '水洗', '淺焙', '卡杜艾', 'SHB', '2024', '1600m', 11.1, 705, '佛手柑, 茶感', '來自巴拿馬著名的波奎特 (Boquete) 產區，SHB 等級代表其生長於極高海拔。這款豆子以其精緻的結構與類似「伯爵茶」的風味特徵而聞名。\n\n【口感特徵】\n● 入口：獨特的佛手柑香氣，酸質優雅且不失活潑。\n● 中段：展現出細膩的紅茶感，口感輕盈且乾淨度極佳。\n● 餘韻：結尾帶有淡淡的柑橘甜味，層次感如同品茗一般深邃。\n\n【感官平衡】\n● 酸度表現：細緻且溫和，具備高級感\n● 苦度表現：極低\n● 酒體 (Body)：輕盈且絲滑\n\n【推薦對象】\n1. 喜歡細緻花果調、不追求強烈衝擊感，而是追求「耐喝與優雅」的愛好者。\n2. 喜歡伯爵茶或柑橘類風味的消費者。\n3. 想嘗試巴拿馬精品咖啡入門風味的玩家。\n\n關鍵關鍵字：佛手柑、清爽茶感、精緻酸、波奎特、高海拔優雅。', 1, 7, NOW(), NOW()),
(7, '薩爾瓦多 帕卡瑪拉', 'https://storage.googleapis.com/production-picture/%E8%96%A9%E7%88%BE%E7%93%A6%E5%A4%9A%20%E5%B8%95%E5%8D%A1%E7%91%AA%E6%8B%89.png', '[]', 580.00, 25, 8, 'roasted_bean', '中美洲', '薩爾瓦多', '聖安娜', '日曬', '中淺焙', '帕卡瑪拉', 'SHB', '2023', '1500m', 10.9, 715, '紅酒, 熟果', '這是一款來自薩爾瓦多聖安娜火山區的帕卡瑪拉 (Pacamara) 特大豆種。採用日曬處理法，將紅酒般的發酵甜感與熟果香氣推向極致。\n\n【口感特徵】\n● 入口：濃郁的紅酒發酵香，伴隨著黑櫻桃與成熟李子的酸甜感。\n● 中段：體感紮實 (Heavy Body)，帶有濃厚的紅糖與熟透熱帶水果調性。\n● 餘韻：結尾溫潤，帶有深色果醬的餘味。\n\n【建議沖煮水溫】：88°C - 90°C，較低的水溫能避免過度萃取導致的苦味，引出深色水果的甜感。\n\n關鍵字：紅酒香, 熟果, 帕卡瑪拉, 厚實口感, 酒香日曬, 強烈甜感', 1, 8, NOW(), NOW()),
(8, '瓜地馬拉 花神', 'https://storage.googleapis.com/production-picture/%E7%93%9C%E5%9C%B0%E9%A6%AC%E6%8B%89%20%E8%8A%B1%E7%A5%9E.png', '[]', 460.00, 60, 22, 'roasted_bean', '中美洲', '瓜地馬拉', '安地瓜', '水洗', '中焙', '波旁', 'SHB', '2024', '1600m', 11.3, 700, '巧克力, 煙燻', '產自安地瓜產區，這款「花神」以其優雅的花香與溫和的煙燻可可調性著稱，是中美洲精品咖啡的經典代表。\n\n【口感特徵】\n● 入口：精緻的茉莉花香，酸質如同青蘋果般爽脆。\n● 中段：展現出堅果與苦甜巧克力的層次，伴隨著極輕微的火山礦物煙燻感。\n● 餘韻：口感絲滑細緻，甜感持久且穩定。\n\n【建議沖煮水溫】：90°C - 92°C，標準水溫能平衡其花香與後段的巧克力調。\n\n關鍵字：安地瓜花神, 巧克力, 煙燻感, 優雅花香, 經典平衡, 絲滑口感', 1, 9, NOW(), NOW()),
(9, '衣索比亞 獅子王', 'https://storage.googleapis.com/production-picture/%E8%A1%A3%E7%B4%A2%E6%AF%94%E4%BA%9E%20%E7%8D%85%E5%AD%90%E7%8E%8B.png', '[]', 490.00, 45, 12, 'roasted_bean', '非洲', '衣索比亞', '谷吉', '日曬', '淺焙', '原生種', 'G1', '2024', '2050m', 10.8, 718, '草莓, 藍莓', '產自谷吉產區的高海拔日曬豆，風味如同其名般奔放。它被公認為「果汁感」最強的豆子之一，充滿濃郁的莓果氣息。\n\n【口感特徵】\n● 入口：強烈的爆發性草莓與藍莓香氣，酸甜感非常活潑。\n● 中段：像是在喝綜合莓果汁，伴隨著桃子與熱帶水果的風味。\n● 餘韻：充滿花蜜般的甜潤，果酸明亮且不尖銳。\n\n【建議沖煮水溫】：92°C - 94°C，高溫能有效激發日曬豆奔放的莓果芳香分子。\n\n關鍵字：草莓, 藍莓, 果汁感, 谷吉日曬, 高酸明亮, 莓果狂熱', 1, 10, NOW(), NOW()),
(10, '哥斯大黎加 莫札特', 'https://storage.googleapis.com/production-picture/%E5%93%A5%E6%96%AF%E5%A4%A7%E9%BB%8E%E5%8A%A0%20%E8%8E%AB%E6%9C%AD%E7%89%B9.png', '[]', 720.00, 15, 12, 'roasted_bean', '中美洲', '哥斯大黎加', '塔拉珠', '葡萄乾蜜處理', '淺焙', '卡杜拉', 'SHB', '2024', '1800m', 10.7, 725, '玫瑰, 葡萄', '音樂家系列中最受歡迎的品項，採用葡萄乾蜜處理，擁有如同「香水」般的強烈辨識度，風味極其華麗。\n\n【口感特徵】\n● 入口：濃郁的玫瑰花香，瞬間填滿口腔。\n● 中段：葡萄乾與草莓醬的甜美發酵感，層次感極度豐富。\n● 餘韻：餘味帶有肉桂與花香的複合氣息，香氣飽滿度極高。\n\n【建議沖煮水溫】：90°C - 92°C，適中的水溫能保留其精緻的香水調性，不至於讓發酵感過於刺鼻。\n\n關鍵字：莫札特, 玫瑰花香, 葡萄乾蜜處理, 音樂家系列, 香水調, 濃郁發酵', 1, 3, NOW(), NOW()),
(11, '盧安達 天空之城', 'https://storage.googleapis.com/production-picture/%E7%9B%A7%E5%AE%89%E9%81%94.png', '[]', 430.00, 80, 0, 'green_bean', '非洲', '盧安達', '西部省', '水洗', '無', '波旁', 'A1', '2024', '1800m', 11.4, 735, '柑橘, 茶感', '來自東非盧安達的高山水洗生豆。這支豆子以乾淨度與茶感著稱，非常適合想要練習控制酸質的烘焙玩家。\n\n【風味預期】\n● 表現：具備新鮮柑橘與黃檸檬的清香，帶有類似大吉嶺紅茶的單寧感與茶韻。\n● 特色：水洗處理極致乾淨，完全無雜味，尾韻帶有紅糖甜感。\n\n【建議沖煮水溫】：(視烘焙度而定) 建議淺焙使用 92°C 以上，中焙使用 88°C - 90°C。\n\n關鍵字：生豆, 茶感, 柑橘, 乾淨度, 盧安達', 1, 4, NOW(), NOW()),
(12, '雲南 普洱', 'https://storage.googleapis.com/production-picture/%E9%9B%B2%E5%8D%97%20%E6%99%AE%E6%B4%B1.png', '[]', 400.00, 30, 8, 'roasted_bean', '亞洲', '中國', '雲南', '日曬', '中淺焙', '卡蒂姆', '一級', '2023', '1500m', 12.0, 695, '木質, 普洱', '雲南產區近年來的力作，日曬處理法結合當地的微氣候，創造出帶有東方普洱茶韻與溫和木質調的獨特風味。\n\n【口感特徵】\n● 入口：沉穩的木質香氣，伴隨著淡淡的普洱茶香，風格獨樹一幟。\n● 中段：帶有果乾與紅糖的微甜，發酵感溫和不刺激。\n● 餘韻：回甘度強，口中會留下淡淡的藥草甜味。\n\n【建議沖煮水溫】：88°C - 91°C，略低的水溫能減少木質纖維可能的苦感，提升回甘。\n\n關鍵字：普洱茶韻, 木質調, 雲南, 日曬處理, 低酸平衡, 獨特風味', 1, 5, NOW(), NOW()),
(13, '夏威夷 可那', 'https://storage.googleapis.com/production-picture/%E5%A4%8F%E5%A8%81%E5%A4%B7%20%E5%8F%AF%E9%82%A3.png', '[]', 950.00, 15, 6, 'roasted_bean', '大洋洲', '美國', '可那區', '水洗', '中焙', '鐵皮卡', '頂級Extra Fancy', '2024', '600m', 11.8, 740, '奶油, 焦糖', '全球最頂級的產區之一，生長於夏威夷火山坡。這款咖啡以其極致的圓潤感與奶油堅果香氣，展現出貴族般的優雅。\n\n【口感特徵】\n● 入口：極致柔和的奶油感，伴隨著夏威夷火山豆的焦糖香氣。\n● 中段：酸質極低且溫潤，細緻的甜度如同楓糖漿般絲滑。\n● 餘韻：乾淨度極高，尾韻悠長且溫暖。\n\n【建議沖煮水溫】：85°C - 88°C，低溫萃取最能體現可那豆如絲緞般的滑順與細膩甜感。\n\n關鍵字：夏威夷可那, 貴族咖啡, 奶油感, 焦糖, 火山土壤, 極低酸度', 1, 6, NOW(), NOW()),
(14, '坦尚尼亞 吉利馬札羅', 'https://storage.googleapis.com/production-picture/%E5%9D%A6%E5%B0%9A%E5%B0%BC%E4%BA%9E%20%E5%90%89%E5%88%A9%E9%A6%AC%E6%9C%AD%E7%BE%85.png', '[]', 460.00, 50, 11, 'roasted_bean', '非洲', '坦尚尼亞', '吉力馬札羅', '水洗', '中焙', '阿拉比卡', 'AA', '2023', '1650m', 10.9, 722, '青蘋果, 萊姆', '產自非洲第一高峰吉力馬札羅山腳下。其高海拔與冷涼氣候培育出這款酸質明亮、口感清脆的咖啡。\n\n【口感特徵】\n● 入口：明亮的青蘋果酸與萊姆皮清香，口水直流的清爽感。\n● 中段：輕盈的Body，帶有野花香氣與蜂蜜般的微甜。\n● 餘韻：收尾乾脆且帶有柑橘皮的清新香氣。\n\n【建議沖煮水溫】：91°C - 93°C，較高溫能幫助釋放高海拔硬豆的明亮酸質。\n\n關鍵字：青蘋果酸, 吉力馬札羅, 明亮活潑, 非洲豆, 清爽口感, 萊姆', 1, 7, NOW(), NOW()),
(15, '印度 季風馬拉巴', 'https://storage.googleapis.com/production-picture/%E5%8D%B0%E5%BA%A6%20%E5%AD%A3%E9%A2%A8%E9%A6%AC%E6%8B%89%E5%B7%B4.png', '[]', 380.00, 120, 33, 'roasted_bean', '亞洲', '印尼', '馬拉巴海岸', '風漬處理', '深焙', '阿拉比卡', 'AA', '2023', '1000m', 13.0, 660, '辛香料, 菸草', '這款豆子經歷了數月的季風吹拂「風漬處理」，模擬古航海時代的風味。是目前知識庫中酸度最低、口感最厚實的代表。\n\n【口感特徵】\n● 入口：強烈的辛香料（如肉桂、胡椒）與烘焙穀物香氣。\n● 中段：完全不帶果酸，具備極高的 Body 與沉穩的菸草、泥土氣息。\n● 餘韻：餘味帶有玄米茶的焦香味，口感極其醇厚。\n\n【建議沖煮水溫】：82°C - 85°C，此豆多為深焙，極低溫可避免焦苦，萃取出醇厚的藥草甜。\n\n關鍵字：風漬處理, 辛香料, 低酸極致, 濃厚Body, 菸草香, 搭配牛奶', 1, 8, NOW(), NOW()),
(16, '宏都拉斯 聖文森', 'https://storage.googleapis.com/production-picture/%E5%AE%8F%E9%83%BD%E6%8B%89%E6%96%AF%20%E8%81%96%E6%96%87%E6%A3%AE.png', '[]', 390.00, 90, 14, 'roasted_bean', '中美洲', '宏都拉斯', '聖芭芭拉', '水洗', '中焙', '帕卡斯', 'SHB', '2024', '1550m', 11.2, 710, '榛果, 甜橙', '聖文森地區的水洗精品，以其高度的平衡感與紮實的甜感聞名，是一款不管什麼溫度喝都非常舒適的全能豆款。\n\n【口感特徵】\n● 入口：清甜的甜橙與軟質柑橘酸，溫和不刺激。\n● 中段：轉化為榛果與焦糖的甜潤感，口感非常圓潤平衡。\n● 餘韻：收尾溫和且甘甜，帶有一絲核果的油脂香。\n\n【建議沖煮水溫】：88°C - 91°C，穩定的中溫最能發揮其全能平衡的特性。\n\n關鍵字：甜橙, 榛果, 全能平衡, 宏都拉斯, 圓潤甜感, 入門首選', 1, 9, NOW(), NOW()),
(17, '祕魯 庫斯科', 'https://storage.googleapis.com/production-picture/%E7%A5%95%E9%AD%AF%20%E5%BA%AB%E6%96%AF%E7%A7%91.png', '[]', 410.00, 65, 9, 'roasted_bean', '南美洲', '祕魯', '庫斯科', '水洗', '中焙', '鐵皮卡', 'SHB', '2023', '1700m', 11.0, 715, '麥芽, 紅糖', '產自高海拔庫斯科產區，這款豆子展現了南美洲純淨的風土。它的特色在於簡單、乾淨、且帶有強烈的麥芽甜味。\n\n【口感特徵】\n● 入口：柔和的柑橘酸調，隨即被強大的麥芽與紅糖甜感包覆。\n● 中段：口感平穩且扎實，帶有淡淡的巧克力基調。\n● 餘韻：清爽回甘，沒有多餘的雜味，呈現高山豆的純淨感。\n\n【建議沖煮水溫】：89°C - 91°C，均勻的水溫有助於麥芽糖甜感的完整釋放。\n\n關鍵字：麥芽甜, 紅糖, 庫斯科, 純淨度, 平易近人', 1, 10, NOW(), NOW()),
(18, '衣索比亞 蓋德奧', 'https://storage.googleapis.com/production-picture/%E8%A1%A3%E7%B4%A2%E6%AF%94%E4%BA%9E%20%E8%93%8B%E5%BE%B7%E5%A5%A7.png', '[]', 440.00, 80, 20, 'roasted_bean', '非洲', '衣索比亞', '蓋德奧', '水洗', '淺焙', '原生種', 'G1', '2024', '1950m', 11.1, 712, '水蜜桃, 軟糖', '如果您喜歡耶加雪菲的精緻，那麼蓋德奧會讓您驚豔。它的風味如同精緻的水果軟糖，酸甜感平衡得恰到好處。\n\n【口感特徵】\n● 入口：迷人的水蜜桃香氣與精緻的白花香。\n● 中段：酸質細膩如同咬下新鮮多汁的蜜桃，甜度高且輕快。\n● 餘韻：餘韻優雅清透，帶有淡淡的佛手柑與水果軟糖甜味。\n\n【建議沖煮水溫】：92°C - 94°C，高溫能有效萃取淺焙豆的花香分子與細緻果酸。\n\n關鍵字：水蜜桃, 水果軟糖, 精緻酸甜, 花香, 少女感', 1, 3, NOW(), NOW()),
(19, '馬拉威 藝伎生豆', 'https://storage.googleapis.com/production-picture/%E9%A6%AC%E6%8B%89%E5%A8%81%20%E8%97%9D%E4%BC%8E.png', '[]', 520.00, 40, 5, 'green_bean', '非洲', '馬拉威', '米蘇庫', '水洗', '無', '藝伎種', 'AAA', '2024', '1850m', 10.6, 728, '茉莉, 柑橘', '這是一款具備藝伎 (Geisha) 貴族血統的非洲生豆。雖然產區不在巴拿馬，但其經典的茉莉花香與柑橘層次依然令人讚嘆。\n\n【風味預期】\n● 表現：優雅的茉莉花香與明亮的柑橘果酸，層次感豐富且具備藝伎品種特有的香氣細緻度。\n● 特色：性價比極高，是想體驗藝伎品種魅力的烘焙玩家的首選。\n\n【建議沖煮水溫】：(烘焙後建議) 91°C - 93°C，以支撐其複雜的層次感。\n\n關鍵字：藝伎品種, 茉莉花香, 生豆, 馬拉威, 精品之王, 高CP值', 1, 4, NOW(), NOW()),
(20, '下架測試產品', 'https://images.unsplash.com/photo-1426260193283-c4daed7c2024', '[]', 100.00, 0, 0, 'roasted_bean', '亞洲', '台灣', '測試產區', '水洗', '中焙', '混種', '三級', '2022', '500m', 14.0, 600, '無', '僅供系統庫存邏輯測試', 0, 3, NOW(), NOW());

-- 5. 訂單資料 (30 筆)
INSERT INTO orders (order_id, user_id, status, total, created_at, status_updated_at) VALUES
(1, 11, '已完成', 1450.00, NOW(), NOW()),
(2, 12, '待付款', 550.00, NOW(), NOW()),
(3, 13, '待出貨', 960.00, NOW(), NOW()),
(4, 14, '已完成', 480.00, NOW(), NOW()),
(5, 15, '已取消', 420.00, NOW(), NOW()),
(6, 16, '待出貨', 1200.00, NOW(), NOW()),
(7, 17, '已完成', 450.00, NOW(), NOW()),
(8, 18, '已完成', 550.00, NOW(), NOW()),
(9, 19, '待付款', 960.00, NOW(), NOW()),
(10, 20, '待出貨', 480.00, NOW(), NOW()),
(11, 21, '已完成', 420.00, NOW(), NOW()),
(12, 22, '已完成', 1200.00, NOW(), NOW()),
(13, 23, '待付款', 350.00, NOW(), NOW()),
(14, 24, '待出貨', 650.00, NOW(), NOW()),
(15, 25, '已完成', 840.00, NOW(), NOW()),
(16, 26, '已完成', 1350.00, NOW(), NOW()),
(17, 27, '待付款', 450.00, NOW(), NOW()),
(18, 28, '待出貨', 550.00, NOW(), NOW()),
(19, 29, '已完成', 960.00, NOW(), NOW()),
(20, 30, '已完成', 420.00, NOW(), NOW()),
(21, 11, '待出貨', 1200.00, NOW(), NOW()),
(22, 12, '已完成', 350.00, NOW(), NOW()),
(23, 13, '待付款', 580.00, NOW(), NOW()),
(24, 14, '待出貨', 460.00, NOW(), NOW()),
(25, 15, '已完成', 490.00, NOW(), NOW()),
(26, 16, '已完成', 470.00, NOW(), NOW()),
(27, 17, '待付款', 430.00, NOW(), NOW()),
(28, 18, '待出貨', 1200.00, NOW(), NOW()),
(29, 19, '已完成', 440.00, NOW(), NOW()),
(30, 20, '待付款', 390.00, NOW(), NOW());

-- 6. 訂單明細 (30 筆，對應上述訂單與產品)
INSERT INTO order_items (order_id, product_id, quantity, price, user_id) VALUES
(1, 1, 2, 450.0, 11), (1, 2, 1, 550.0, 11), (2, 2, 1, 550.0, 12), (3, 4, 2, 480.0, 13), (4, 4, 1, 480.0, 14),
(5, 3, 1, 420.0, 15), (6, 13, 1, 1200.0, 16), (7, 1, 1, 450.0, 17), (8, 2, 1, 550.0, 18), (9, 4, 2, 480.0, 19),
(10, 4, 1, 480.0, 20), (11, 3, 1, 420.0, 21), (12, 13, 1, 1200.0, 22), (13, 5, 1, 350.0, 23), (14, 6, 1, 650.0, 24),
(15, 1, 1, 450.0, 25), (15, 16, 1, 390.0, 25), (16, 1, 3, 450.0, 26), (17, 1, 1, 450.0, 27), (18, 2, 1, 550.0, 28),
(19, 4, 2, 480.0, 29), (20, 3, 1, 420.0, 30), (21, 13, 1, 1200.0, 11), (22, 5, 1, 350.0, 12), (23, 7, 1, 580.0, 13),
(24, 8, 1, 460.0, 14), (25, 9, 1, 490.0, 15), (26, 10, 1, 470.0, 16), (27, 11, 1, 430.0, 17), (28, 13, 1, 1200.0, 18),
(29, 15, 1, 440.0, 19), (30, 16, 1, 390.0, 20);
