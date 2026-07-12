-- Adds a "ready" intermediate state between draft and published, plus the
-- start date/time a published quiz becomes available to students.
ALTER TABLE quizzes
    MODIFY COLUMN status ENUM('draft', 'ready', 'published') NOT NULL DEFAULT 'draft';

ALTER TABLE quizzes
    ADD COLUMN scheduled_start DATETIME NULL AFTER status;
