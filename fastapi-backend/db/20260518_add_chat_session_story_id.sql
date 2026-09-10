USE springcloud;

ALTER TABLE chat_sessions
    ADD COLUMN story_id BIGINT NULL AFTER user_id,
    ADD KEY idx_chat_sessions_story_id (story_id),
    ADD CONSTRAINT fk_chat_sessions_story
        FOREIGN KEY (story_id) REFERENCES stories(id)
        ON DELETE SET NULL;
