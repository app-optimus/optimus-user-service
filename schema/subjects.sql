CREATE TABLE IF NOT EXISTS subjects (
    subject_id      VARCHAR(12)  NOT NULL,
    entity_id       VARCHAR(12)  NOT NULL,
    class_id        VARCHAR(12)  NOT NULL,
    subject_name    VARCHAR(100) NOT NULL,
    display_order   INT          NOT NULL DEFAULT 0,
    active          TINYINT(1)   NOT NULL DEFAULT 1,
    created_by      VARCHAR(16)  NOT NULL,
    updated_by      VARCHAR(16)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (subject_id),
    UNIQUE KEY uq_class_subject_name (class_id, subject_name, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
