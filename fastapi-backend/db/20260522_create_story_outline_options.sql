USE springcloud;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS story_outline_options (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    option_type VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    sort_order INT NOT NULL DEFAULT 0,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_story_outline_option_type_name (option_type, name),
    KEY idx_story_outline_options_type_enabled (option_type, enabled),
    KEY idx_story_outline_options_sort (sort_order, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO story_outline_options (option_type, name, description, sort_order, enabled)
VALUES
    ('GENRE', '科幻', '科技、未来、人工智能、时间线等题材。', 10, 1),
    ('GENRE', '奇幻', '异世界、魔法、神话、幻想冒险等题材。', 20, 1),
    ('GENRE', '悬疑', '谜案、反转、心理博弈、隐秘真相等题材。', 30, 1),
    ('GENRE', '爱情', '情感成长、关系拉扯、命运羁绊等题材。', 40, 1),
    ('GENRE', '热血', '成长、战斗、团队、逆袭等题材。', 50, 1),
    ('GENRE', '都市', '现代城市、职场、家族、社会议题等题材。', 60, 1),
    ('GENRE', '校园', '校园生活、青春成长、社团与友情等题材。', 70, 1),
    ('STYLE', '国漫电影感', '高质感光影、电影级构图、细腻角色表演。', 10, 1),
    ('STYLE', '日系赛璐璐', '清晰线稿、平涂色块、动画番剧视觉。', 20, 1),
    ('STYLE', '厚涂奇幻', '浓厚笔触、奇幻氛围、强烈光影层次。', 30, 1),
    ('STYLE', '黑白悬疑漫画', '高对比黑白、压迫感构图、悬疑叙事氛围。', 40, 1),
    ('STYLE', '赛博朋克霓虹', '霓虹灯光、未来都市、冷暖强对比。', 50, 1),
    ('STYLE', '水彩治愈系', '柔和色彩、水彩肌理、温暖轻盈氛围。', 60, 1),
    ('STYLE', '复古港漫', '高饱和色彩、强烈动作张力、复古漫画气质。', 70, 1)
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    sort_order = VALUES(sort_order),
    enabled = VALUES(enabled);
