CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id        VARCHAR(12)  NOT NULL,
    entity_id      VARCHAR(12)  NOT NULL,
    class_id       VARCHAR(12)  NOT NULL,
    section_id     VARCHAR(12)  NOT NULL,
    title          VARCHAR(200) NOT NULL,
    description    VARCHAR(500) NULL,
    status         ENUM('draft', 'ready', 'published') NOT NULL DEFAULT 'draft',
    scheduled_start DATETIME    NULL,
    active         TINYINT(1)   NOT NULL DEFAULT 1,
    created_by     VARCHAR(16)  NOT NULL,
    updated_by     VARCHAR(16)  NOT NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (quiz_id),
    KEY idx_quizzes_entity_active (entity_id, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quiz_questions (
    question_id    VARCHAR(12)  NOT NULL,
    quiz_id        VARCHAR(12)  NOT NULL,
    entity_id      VARCHAR(12)  NOT NULL,
    question_type  VARCHAR(50)  NOT NULL,
    question_text  VARCHAR(1000) NOT NULL,
    config         JSON         NOT NULL,
    answer_key     JSON         NULL,
    grading_mode   ENUM('auto', 'manual') NOT NULL DEFAULT 'auto',
    marks          INT          NOT NULL DEFAULT 1,
    display_order  INT          NOT NULL DEFAULT 0,
    active         TINYINT(1)   NOT NULL DEFAULT 1,
    created_by     VARCHAR(16)  NOT NULL,
    updated_by     VARCHAR(16)  NOT NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (question_id),
    KEY idx_quiz_questions_quiz_active (quiz_id, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
