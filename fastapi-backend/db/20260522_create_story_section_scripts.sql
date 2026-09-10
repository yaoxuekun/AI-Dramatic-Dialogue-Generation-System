USE springcloud;

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
