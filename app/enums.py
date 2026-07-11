from enum import Enum


class Tables:
    user_authentication = "user_authentication"
    user_details = "user_details"
    entity_permissions = "entity_permissions"
    user_entity_details = "user_entity_details"
    entity_details = "entity_details"
    entity_classes = "entity_classes"
    entity_class_sections = "entity_class_sections"
    user_entity_class_details = "user_entity_class_details"
    question_templates = "question_templates"
    quizzes = "quizzes"
    quiz_questions = "quiz_questions"


class UserTypes(str, Enum):
    chief_admin = "chief admin"
    entity_admin = "entity admin"   # principal
    user = "user"   # both teacher and students


class UserRoles(str, Enum):
    principal = "principal"
    teacher = "teacher"
    student = "student"


class QuestionTypes(str, Enum):
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    one_word = "one_word"
    number = "number"
    long_text = "long_text"


class GradingModes(str, Enum):
    auto = "auto"
    manual = "manual"


class QuizStatus(str, Enum):
    draft = "draft"
    published = "published"


# A quiz needs enough questions to be meaningful but few enough that grading
# and the builder UI stay fast and simple.
QUIZ_MIN_QUESTIONS = 3
QUIZ_MAX_QUESTIONS = 20
