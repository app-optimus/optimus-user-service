CREATE TABLE IF NOT EXISTS study_materials (
    material_id     VARCHAR(12)  NOT NULL,
    entity_id       VARCHAR(12)  NOT NULL,
    class_id        VARCHAR(12)  NOT NULL,
    -- NULL means the material applies to every section of the class.
    section_id      VARCHAR(12)  NULL,
    subject_id      VARCHAR(12)  NOT NULL,
    material_type   ENUM('lecture', 'notes', 'sample_quiz') NOT NULL,
    title           VARCHAR(200) NOT NULL,
    description     VARCHAR(500) NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    file_size       INT          NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    active          TINYINT(1)   NOT NULL DEFAULT 1,
    created_by      VARCHAR(16)  NOT NULL,
    updated_by      VARCHAR(16)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (material_id),
    KEY idx_study_materials_entity_active (entity_id, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
