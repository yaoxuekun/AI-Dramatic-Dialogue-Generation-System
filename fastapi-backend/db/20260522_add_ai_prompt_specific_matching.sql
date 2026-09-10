USE springcloud;

SET NAMES utf8mb4;

ALTER TABLE ai_prompts
    ADD COLUMN base_prompt_key VARCHAR(100) NOT NULL DEFAULT '' AFTER prompt_key,
    ADD COLUMN prompt_scope VARCHAR(20) NOT NULL DEFAULT 'DEFAULT' AFTER base_prompt_key,
    ADD COLUMN match_genre VARCHAR(100) AFTER prompt_scope,
    ADD COLUMN match_style VARCHAR(100) AFTER match_genre,
    ADD COLUMN priority INT NOT NULL DEFAULT 0 AFTER match_style,
    ADD KEY idx_ai_prompts_base_scope (base_prompt_key, prompt_scope, enabled),
    ADD KEY idx_ai_prompts_match (base_prompt_key, match_genre, match_style);

UPDATE ai_prompts
SET base_prompt_key = prompt_key,
    prompt_scope = 'DEFAULT',
    priority = 0
WHERE base_prompt_key = '';
