USE springcloud;

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
