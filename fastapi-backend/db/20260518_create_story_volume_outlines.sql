USE springcloud;

CREATE TABLE IF NOT EXISTS story_volume_outlines (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    story_id BIGINT NOT NULL,
    volume_number INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    content LONGTEXT,
    ending_hook TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_story_volume_number (story_id, volume_number),
    KEY idx_story_volume_outlines_story_id (story_id),
    CONSTRAINT fk_story_volume_outlines_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
