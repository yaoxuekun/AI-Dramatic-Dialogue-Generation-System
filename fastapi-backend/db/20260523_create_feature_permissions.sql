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
