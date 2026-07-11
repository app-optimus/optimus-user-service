from fastapi import APIRouter, Request

from app.core import login_required
from app.services.question_templates import QuestionTemplateService
from app.utils import standard_response_generator

question_templates = APIRouter()


@question_templates.get("/")
@login_required
async def _get_question_templates(request: Request):
    processor = QuestionTemplateService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_question_templates()
    return standard_response_generator(success, message, status_code, data)
