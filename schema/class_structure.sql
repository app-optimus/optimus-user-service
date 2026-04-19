CREATE TABLE IF NOT EXISTS entity_classes (
    class_id        VARCHAR(12)  NOT NULL,
    entity_id       VARCHAR(12)  NOT NULL,
    class_name      VARCHAR(100) NOT NULL,
    display_order   INT          NOT NULL DEFAULT 0,
    active          TINYINT(1)   NOT NULL DEFAULT 1,
    created_by      VARCHAR(16)  NOT NULL,
    updated_by      VARCHAR(16)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (class_id),
    UNIQUE KEY uq_entity_class_name (entity_id, class_name, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS entity_class_sections (
    section_id      VARCHAR(12)  NOT NULL,
    class_id        VARCHAR(12)  NOT NULL,
    entity_id       VARCHAR(12)  NOT NULL,
    section_name    VARCHAR(100) NOT NULL,
    display_order   INT          NOT NULL DEFAULT 0,
    active          TINYINT(1)   NOT NULL DEFAULT 1,
    created_by      VARCHAR(16)  NOT NULL,
    updated_by      VARCHAR(16)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (section_id),
    UNIQUE KEY uq_class_section_name (class_id, section_name, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
