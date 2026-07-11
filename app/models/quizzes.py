from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from app.enums import GradingModes, QuestionTypes, QuizStatus


class CreateQuizModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: str = Field(min_length=12, max_length=12)
    section_id: str = Field(min_length=12, max_length=12)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)


class UpdateQuizModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    quiz_id: str = Field(min_length=12, max_length=12)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if self.title is None and self.description is None:
            raise ValueError("At least one of title or description must be provided")
        return self


class DeleteQuizModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    quiz_id: str = Field(min_length=12, max_length=12)


class PublishQuizModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    quiz_id: str = Field(min_length=12, max_length=12)


class GetQuizzes(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    class_id: Optional[str] = None
    section_id: Optional[str] = None
    status: Optional[QuizStatus] = None


class GetQuizDetail(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    quiz_id: str = Field(min_length=12, max_length=12)


def _validate_question_shape(question_type: QuestionTypes, config: dict, answer_key: Any, grading_mode: GradingModes):
    """
    Shared per-type validation for question config/answer_key, used by both
    add and update models so a question can never be persisted in a shape
    the quiz builder / grading logic doesn't expect.
    """
    if question_type in (QuestionTypes.single_choice, QuestionTypes.multiple_choice):
        options = config.get("options")
        if not isinstance(options, list) or len(options) < 2:
            raise ValueError(f"{question_type.value} requires at least 2 options")

        if question_type == QuestionTypes.single_choice:
            if not isinstance(answer_key, int) or not (0 <= answer_key < len(options)):
                raise ValueError("single_choice answer_key must be a valid option index")
        else:
            if not isinstance(answer_key, list) or not answer_key:
                raise ValueError("multiple_choice answer_key must be a non-empty list of option indexes")
            if any(not isinstance(i, int) or not (0 <= i < len(options)) for i in answer_key):
                raise ValueError("multiple_choice answer_key must contain valid option indexes")

    elif question_type == QuestionTypes.one_word:
        accepted_answers = None
        if isinstance(answer_key, dict):
            accepted_answers = answer_key.get("accepted_answers")
        if not isinstance(accepted_answers, list) or not accepted_answers:
            raise ValueError("one_word answer_key must include a non-empty accepted_answers list")

    elif question_type == QuestionTypes.number:
        if not isinstance(answer_key, dict) or not isinstance(answer_key.get("expected_value"), (int, float)):
            raise ValueError("number answer_key must include a numeric expected_value")
        tolerance = answer_key.get("tolerance")
        if tolerance is not None and (not isinstance(tolerance, (int, float)) or tolerance < 0):
            raise ValueError("number answer_key tolerance must be a non-negative number")

    elif question_type == QuestionTypes.long_text:
        if answer_key is not None:
            raise ValueError("long_text questions must not have an answer_key - they are graded manually")
        if grading_mode != GradingModes.manual:
            raise ValueError("long_text questions must use manual grading")
        max_length = config.get("max_length", 1000)
        if not isinstance(max_length, int) or not (0 < max_length <= 1000):
            raise ValueError("long_text config.max_length must be between 1 and 1000")


class AddQuestionModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    quiz_id: str = Field(min_length=12, max_length=12)
    question_type: QuestionTypes
    question_text: str = Field(min_length=1, max_length=1000)
    marks: int = Field(default=1, ge=1)
    grading_mode: GradingModes = GradingModes.auto
    config: dict = Field(default_factory=dict)
    answer_key: Optional[Union[int, float, str, List[Any], dict]] = None

    @model_validator(mode="after")
    def validate_question_shape(self):
        if self.question_type == QuestionTypes.long_text:
            self.grading_mode = GradingModes.manual
        _validate_question_shape(self.question_type, self.config, self.answer_key, self.grading_mode)
        return self


class UpdateQuestionModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    quiz_id: str = Field(min_length=12, max_length=12)
    question_id: str = Field(min_length=12, max_length=12)
    question_type: QuestionTypes
    question_text: str = Field(min_length=1, max_length=1000)
    marks: int = Field(default=1, ge=1)
    grading_mode: GradingModes = GradingModes.auto
    config: dict = Field(default_factory=dict)
    answer_key: Optional[Union[int, float, str, List[Any], dict]] = None

    @model_validator(mode="after")
    def validate_question_shape(self):
        if self.question_type == QuestionTypes.long_text:
            self.grading_mode = GradingModes.manual
        _validate_question_shape(self.question_type, self.config, self.answer_key, self.grading_mode)
        return self


class DeleteQuestionModel(BaseModel):
    entity_id: str = Field(min_length=12, max_length=12)
    quiz_id: str = Field(min_length=12, max_length=12)
    question_id: str = Field(min_length=12, max_length=12)
