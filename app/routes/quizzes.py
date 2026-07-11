from fastapi import APIRouter, Depends, Request

from app.core import login_required
from app.models.quizzes import (
    AddQuestionModel,
    CreateQuizModel,
    DeleteQuestionModel,
    DeleteQuizModel,
    GetQuizDetail,
    GetQuizzes,
    PublishQuizModel,
    UpdateQuestionModel,
    UpdateQuizModel,
)
from app.services.quizzes import QuizService
from app.utils import standard_response_generator

quizzes = APIRouter()


@quizzes.get("/")
@login_required
async def _get_quizzes(request: Request, query_args: GetQuizzes = Depends()):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_quizzes(
        query_args.entity_id,
        query_args.class_id,
        query_args.section_id,
        query_args.status.value if query_args.status else None,
    )
    return standard_response_generator(success, message, status_code, data)


@quizzes.get("/detail")
@login_required
async def _get_quiz_detail(request: Request, query_args: GetQuizDetail = Depends()):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_quiz_detail(
        query_args.entity_id, query_args.quiz_id
    )
    return standard_response_generator(success, message, status_code, data)


@quizzes.post("/")
@login_required
async def _create_quiz(request: Request, data: CreateQuizModel):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, response_data = await processor.create_quiz(data.model_dump())
    return standard_response_generator(success, message, status_code, response_data)


@quizzes.patch("/")
@login_required
async def _update_quiz(request: Request, data: UpdateQuizModel):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.update_quiz(
        data.entity_id, data.quiz_id, data.model_dump(exclude_none=True)
    )
    return standard_response_generator(success, message, status_code)


@quizzes.delete("/")
@login_required
async def _delete_quiz(request: Request, data: DeleteQuizModel):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.delete_quiz(data.entity_id, data.quiz_id)
    return standard_response_generator(success, message, status_code)


@quizzes.post("/question")
@login_required
async def _add_question(request: Request, data: AddQuestionModel):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    payload = data.model_dump()
    payload["question_type"] = data.question_type.value
    payload["grading_mode"] = data.grading_mode.value
    success, message, status_code, response_data = await processor.add_question(
        data.entity_id, data.quiz_id, payload
    )
    return standard_response_generator(success, message, status_code, response_data)


@quizzes.patch("/question")
@login_required
async def _update_question(request: Request, data: UpdateQuestionModel):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    payload = data.model_dump()
    payload["question_type"] = data.question_type.value
    payload["grading_mode"] = data.grading_mode.value
    success, message, status_code = await processor.update_question(
        data.entity_id, data.quiz_id, data.question_id, payload
    )
    return standard_response_generator(success, message, status_code)


@quizzes.delete("/question")
@login_required
async def _delete_question(request: Request, data: DeleteQuestionModel):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.delete_question(
        data.entity_id, data.quiz_id, data.question_id
    )
    return standard_response_generator(success, message, status_code)


@quizzes.post("/publish")
@login_required
async def _publish_quiz(request: Request, data: PublishQuizModel):
    processor = QuizService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code = await processor.publish_quiz(data.entity_id, data.quiz_id)
    return standard_response_generator(success, message, status_code)
