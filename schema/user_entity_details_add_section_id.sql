-- Students were previously only linked to a class (class_id) with no way to
-- tell which section within that class they belong to. This adds the missing
-- link so students can be grouped/counted sectionwise (e.g. for dashboards).
ALTER TABLE user_entity_details
    ADD COLUMN section_id VARCHAR(12) NULL AFTER class_id;
