CREATE TABLE IF NOT EXISTS question_templates (
    template_id           VARCHAR(12)  NOT NULL,
    template_code         VARCHAR(50)  NOT NULL,
    template_name         VARCHAR(100) NOT NULL,
    description           VARCHAR(255) NOT NULL,
    default_grading_mode  ENUM('auto', 'manual') NOT NULL DEFAULT 'auto',
    config_schema         JSON         NOT NULL,
    sample_question       JSON         NOT NULL,
    display_order         INT          NOT NULL DEFAULT 0,
    active                 TINYINT(1)   NOT NULL DEFAULT 1,
    created_by             VARCHAR(16)  NOT NULL,
    updated_by             VARCHAR(16)  NOT NULL,
    created_at              TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (template_id),
    UNIQUE KEY uq_template_code (template_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO question_templates (
    template_id, template_code, template_name, description, default_grading_mode,
    config_schema, sample_question, display_order, active, created_by, updated_by
) VALUES
(
    'qtpl1sngchc0', 'single_choice', 'Single Choice',
    'Student picks exactly one correct option out of several.',
    'auto',
    JSON_OBJECT('options', 'list of choice texts (min 2)', 'answer_key', 'index of the correct option'),
    JSON_OBJECT(
        'question_text', 'Which planet is known as the Red Planet?',
        'options', JSON_ARRAY('Earth', 'Mars', 'Jupiter', 'Venus'),
        'answer', 'Mars'
    ),
    1, 1, 'global-dev-user', 'global-dev-user'
),
(
    'qtpl2mltchc0', 'multiple_choice', 'Multiple Choice',
    'Student can pick one or more correct options out of several.',
    'auto',
    JSON_OBJECT('options', 'list of choice texts (min 2)', 'answer_key', 'list of correct option indexes'),
    JSON_OBJECT(
        'question_text', 'Which of the following are prime numbers?',
        'options', JSON_ARRAY('2', '4', '5', '9'),
        'answer', JSON_ARRAY('2', '5')
    ),
    2, 1, 'global-dev-user', 'global-dev-user'
),
(
    'qtpl3onewrd0', 'one_word', 'One Word Answer',
    'Student types a single short word or phrase; matched against accepted answers.',
    'auto',
    JSON_OBJECT('accepted_answers', 'list of acceptable answer strings', 'case_sensitive', 'boolean, default false'),
    JSON_OBJECT(
        'question_text', 'What is the chemical symbol for water?',
        'answer', 'H2O'
    ),
    3, 1, 'global-dev-user', 'global-dev-user'
),
(
    'qtpl4numbr00', 'number', 'Number Answer',
    'Student enters a numeric answer; matched exactly or within a tolerance.',
    'auto',
    JSON_OBJECT('expected_value', 'numeric answer', 'tolerance', 'optional +/- allowed deviation'),
    JSON_OBJECT(
        'question_text', 'How many continents are there on Earth?',
        'answer', 7
    ),
    4, 1, 'global-dev-user', 'global-dev-user'
),
(
    'qtpl5lngtxt0', 'long_text', 'Long Text Answer',
    'Student writes a free-form answer (up to 1000 characters); requires manual grading.',
    'manual',
    JSON_OBJECT('max_length', 1000),
    JSON_OBJECT(
        'question_text', 'Explain the water cycle in your own words.',
        'answer', NULL
    ),
    5, 1, 'global-dev-user', 'global-dev-user'
);
