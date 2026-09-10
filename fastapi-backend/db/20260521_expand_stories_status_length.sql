USE springcloud;

ALTER TABLE stories
    MODIFY COLUMN status VARCHAR(50) NOT NULL DEFAULT 'draft';
