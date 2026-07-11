from fastapi import APIRouter, Depends, Request

from app.core import login_required
from app.models.dashboard import GetHeadcountSummary, GetQuizSummary, GetStudentSectionCounts
from app.services.dashboard import DashboardService
from app.utils import standard_response_generator

dashboard = APIRouter()


@dashboard.get("/student-section-counts")
@login_required
async def _get_student_section_counts(request: Request, query_args: GetStudentSectionCounts = Depends()):
    processor = DashboardService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_student_counts_by_class_section(
        query_args.entity_id
    )
    return standard_response_generator(success, message, status_code, data)


@dashboard.get("/headcount-summary")
@login_required
async def _get_headcount_summary(request: Request, query_args: GetHeadcountSummary = Depends()):
    processor = DashboardService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_headcount_summary(query_args.entity_id)
    return standard_response_generator(success, message, status_code, data)


@dashboard.get("/quiz-summary")
@login_required
async def _get_quiz_summary(request: Request, query_args: GetQuizSummary = Depends()):
    processor = DashboardService(db=request.app.db, logger=request.app.logger, x_user=request.app.user)
    success, message, status_code, data = await processor.fetch_quiz_summary(query_args.entity_id)
    return standard_response_generator(success, message, status_code, data)
