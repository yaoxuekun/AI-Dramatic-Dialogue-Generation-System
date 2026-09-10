USE springcloud;

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
