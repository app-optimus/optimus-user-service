-- entity_classes.class_id is VARCHAR(12) (nanoid length=12), but
-- user_entity_details.class_id was left at VARCHAR(10), so any real class_id
-- would fail to insert. Widen it to match.
ALTER TABLE user_entity_details
    MODIFY COLUMN class_id VARCHAR(12) NULL;
