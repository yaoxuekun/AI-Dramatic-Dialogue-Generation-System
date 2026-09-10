USE springcloud;

ALTER TABLE users
    ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'USER' AFTER avatar_path;

ALTER TABLE users
    ADD INDEX idx_users_role (role);

UPDATE users
SET role = 'ROOT'
WHERE username = 'root';
