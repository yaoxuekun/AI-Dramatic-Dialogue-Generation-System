-- AI漫剧生成系统数据库初始化脚本
-- 默认库名按 config.txt/application.yml 使用 springcloud。
-- 如需使用设计文档中的 aisay_manga，可将下方 springcloud 替换为 aisay_manga 后执行。

CREATE DATABASE IF NOT EXISTS springcloud
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'aisay'@'localhost' IDENTIFIED BY 'aisay_pass';
CREATE USER IF NOT EXISTS 'aisay'@'%' IDENTIFIED BY 'aisay_pass';
GRANT ALL PRIVILEGES ON springcloud.* TO 'aisay'@'localhost';
GRANT ALL PRIVILEGES ON springcloud.* TO 'aisay'@'%';
FLUSH PRIVILEGES;

USE springcloud;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_path VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    preferences JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_users_username (username),
    UNIQUE KEY uk_users_email (email),
    KEY idx_users_email (email),
    KEY idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    story_id BIGINT,
    session_key VARCHAR(100) NOT NULL,
    title VARCHAR(200),
    context_data JSON,
    current_stage VARCHAR(50) DEFAULT 'INITIAL',
    progress_percentage INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_chat_sessions_session_key (session_key),
    KEY idx_chat_sessions_user_id (user_id),
    KEY idx_chat_sessions_story_id (story_id),
    KEY idx_chat_sessions_status (status),
    KEY idx_chat_sessions_last_active (last_active),
    CONSTRAINT fk_chat_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_messages_session_id (session_id),
    KEY idx_messages_created_at (created_at),
    CONSTRAINT fk_messages_session
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    genre VARCHAR(100),
    style VARCHAR(100),
    synopsis TEXT,
    full_content LONGTEXT,
    cover_image_path VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    view_count INT NOT NULL DEFAULT 0,
    like_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_stories_user_id (user_id),
    KEY idx_stories_status (status),
    FULLTEXT KEY ft_stories_title_synopsis (title, synopsis),
    CONSTRAINT fk_stories_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE chat_sessions
    ADD CONSTRAINT fk_chat_sessions_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS characters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100),
    description TEXT,
    personality TEXT,
    appearance JSON,
    KEY idx_characters_story_id (story_id),
    CONSTRAINT fk_characters_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS story_volume_outlines (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    volume_number INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    content LONGTEXT,
    ending_hook TEXT,
    detailed_content LONGTEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_story_volume_number (story_id, volume_number),
    KEY idx_story_volume_outlines_story_id (story_id),
    CONSTRAINT fk_story_volume_outlines_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS story_volume_sections (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    volume_id BIGINT NOT NULL,
    section_number INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    content LONGTEXT,
    ending_hook TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_volume_section_number (volume_id, section_number),
    KEY idx_story_volume_sections_story_id (story_id),
    KEY idx_story_volume_sections_volume_id (volume_id),
    CONSTRAINT fk_story_volume_sections_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_story_volume_sections_volume
        FOREIGN KEY (volume_id) REFERENCES story_volume_outlines(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS story_assets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    image_prompt TEXT,
    image_path VARCHAR(500),
    audio_path VARCHAR(500),
    first_section_id BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_story_asset_name (story_id, asset_type, name),
    KEY idx_story_assets_story_id (story_id),
    KEY idx_story_assets_first_section_id (first_section_id),
    CONSTRAINT fk_story_assets_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_story_assets_first_section
        FOREIGN KEY (first_section_id) REFERENCES story_volume_sections(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS story_section_assets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    section_id BIGINT NOT NULL,
    asset_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_section_asset (section_id, asset_id),
    KEY idx_story_section_assets_story_id (story_id),
    KEY idx_story_section_assets_section_id (section_id),
    KEY idx_story_section_assets_asset_id (asset_id),
    CONSTRAINT fk_story_section_assets_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_story_section_assets_section
        FOREIGN KEY (section_id) REFERENCES story_volume_sections(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_story_section_assets_asset
        FOREIGN KEY (asset_id) REFERENCES story_assets(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS story_section_scripts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    section_id BIGINT NOT NULL,
    shot_number INT NOT NULL,
    duration_seconds INT NOT NULL,
    shot_type VARCHAR(50) NOT NULL,
    camera_movement VARCHAR(100),
    action TEXT NOT NULL,
    dialogue TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_section_script_shot (section_id, shot_number),
    KEY idx_story_section_scripts_story_id (story_id),
    KEY idx_story_section_scripts_section_id (section_id),
    CONSTRAINT fk_story_section_scripts_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_story_section_scripts_section
        FOREIGN KEY (section_id) REFERENCES story_volume_sections(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

CREATE TABLE IF NOT EXISTS ai_prompts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prompt_key VARCHAR(100) NOT NULL,
    base_prompt_key VARCHAR(100) NOT NULL DEFAULT '',
    prompt_scope VARCHAR(20) NOT NULL DEFAULT 'DEFAULT',
    match_genre VARCHAR(100),
    match_style VARCHAR(100),
    priority INT NOT NULL DEFAULT 0,
    prompt_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    description VARCHAR(1000),
    template_content LONGTEXT NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_prompts_key (prompt_key),
    KEY idx_ai_prompts_category (category),
    KEY idx_ai_prompts_enabled (enabled),
    KEY idx_ai_prompts_base_scope (base_prompt_key, prompt_scope, enabled),
    KEY idx_ai_prompts_match (base_prompt_key, match_genre, match_style)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_prompt_parameters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prompt_id BIGINT NOT NULL,
    direction VARCHAR(20) NOT NULL,
    param_key VARCHAR(100) NOT NULL,
    param_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    required_flag TINYINT(1) NOT NULL DEFAULT 1,
    description VARCHAR(1000),
    example_value VARCHAR(1000),
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_prompt_param (prompt_id, direction, param_key),
    KEY idx_ai_prompt_parameters_prompt_id (prompt_id),
    KEY idx_ai_prompt_parameters_direction (direction),
    CONSTRAINT fk_ai_prompt_parameters_prompt
        FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS feature_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    feature_key VARCHAR(100) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(1000),
    allowed_roles VARCHAR(100) NOT NULL DEFAULT 'ROOT',
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_feature_permissions_key (feature_key),
    KEY idx_feature_permissions_category (category),
    KEY idx_feature_permissions_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO feature_permissions (feature_key, feature_name, category, description, allowed_roles, enabled, sort_order)
VALUES
    ('chat.use', '对话系统', '对话', '创建对话、查看对话历史、发送消息和删除对话。', 'ADMIN,ROOT,USER', 1, 10),
    ('story.list', '漫剧列表', '漫剧', '查看当前用户的漫剧列表。', 'ADMIN,ROOT,USER', 1, 20),
    ('story.detail', '漫剧详情', '漫剧', '查看当前用户的漫剧详情、剧情大纲、分卷、小节和资产。', 'ADMIN,ROOT,USER', 1, 30),
    ('story.generate', '生成剧情大纲', '漫剧', '根据题材、风格和可选剧情创建漫剧并异步生成剧情大纲。', 'ADMIN,ROOT,USER', 1, 40),
    ('story.updateBasic', '编辑漫剧基础信息', '漫剧', '修改漫剧标题、题材、风格和故事摘要。', 'ADMIN,ROOT,USER', 1, 50),
    ('story.updateDetail', '手动编辑剧情大纲', '漫剧', '手动保存故事摘要、剧情大纲和主要角色设定。', 'ADMIN,ROOT,USER', 1, 60),
    ('story.reviseOutline', '自动修改剧情大纲', '漫剧', '根据用户修改意见异步调用 AI 修改剧情大纲。', 'ADMIN,ROOT,USER', 1, 70),
    ('story.generateVolumeOutline', '生成分卷大纲', '漫剧', '根据剧情大纲异步生成分卷大纲。', 'ADMIN,ROOT,USER', 1, 80),
    ('story.reviseVolumeOutline', '自动修改分卷大纲', '漫剧', '根据修改意见异步调用 AI 重写分卷大纲。', 'ADMIN,ROOT,USER', 1, 90),
    ('story.updateVolumeOutline', '手动编辑分卷大纲', '漫剧', '手动保存分卷大纲列表。', 'ADMIN,ROOT,USER', 1, 100),
    ('story.generateVolumeSections', '生成小节故事', '漫剧', '根据分卷大纲异步生成小节故事细节。', 'ADMIN,ROOT,USER', 1, 110),
    ('story.generateSectionAssets', '生成人物/场景图片', '漫剧', '根据小节内容识别人物和场景，并异步生成或复用图片资产。', 'ADMIN,ROOT,USER', 1, 120),
    ('story.generateSectionScript', '生成故事脚本', '漫剧', '根据小节故事异步生成分镜脚本。', 'ADMIN,ROOT,USER', 1, 130),
    ('story.uploadAssetAudio', '上传人物声音', '漫剧', '为人物资产上传用户准备的音频文件。', 'ADMIN,ROOT,USER', 1, 140),
    ('story.delete', '删除漫剧', '漫剧', '删除当前用户拥有的漫剧。', 'ADMIN,ROOT,USER', 1, 150),
    ('outlineConfig.manage', '大纲配置管理', '系统管理', '管理剧情大纲题材和漫剧风格配置。', 'ADMIN,ROOT', 1, 210),
    ('prompt.manage', 'Prompt 管理', '系统管理', '管理默认 Prompt 和特定 Prompt。', 'ADMIN,ROOT', 1, 220),
    ('user.manage', '用户权限管理', '系统管理', '查看用户列表并设置用户角色。', 'ROOT', 1, 230),
    ('featurePermission.manage', '功能权限管理', '系统管理', '设置各功能操作允许哪些角色使用。', 'ROOT', 1, 240)
ON DUPLICATE KEY UPDATE
    feature_name = VALUES(feature_name),
    category = VALUES(category),
    description = VALUES(description),
    enabled = VALUES(enabled),
    sort_order = VALUES(sort_order);

CREATE TABLE IF NOT EXISTS scenes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    scene_number INT NOT NULL,
    setting VARCHAR(500),
    description TEXT,
    visual_elements JSON,
    KEY idx_scenes_story_id (story_id),
    KEY idx_scenes_story_scene_number (story_id, scene_number),
    CONSTRAINT fk_scenes_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dialogues (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    scene_id BIGINT NOT NULL,
    character_id BIGINT,
    content TEXT NOT NULL,
    `order` INT NOT NULL DEFAULT 0,
    KEY idx_dialogues_scene_id (scene_id),
    KEY idx_dialogues_character_id (character_id),
    KEY idx_dialogues_scene_order (scene_id, `order`),
    CONSTRAINT fk_dialogues_scene
        FOREIGN KEY (scene_id) REFERENCES scenes(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_dialogues_character
        FOREIGN KEY (character_id) REFERENCES characters(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
