USE springcloud;

ALTER TABLE story_volume_outlines
    ADD COLUMN detailed_content LONGTEXT NULL AFTER ending_hook;
