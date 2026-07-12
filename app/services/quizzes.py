import json
from http import HTTPStatus

from app.enums import QUIZ_MAX_QUESTIONS, QUIZ_MIN_QUESTIONS, QuizStatus, Tables
from app.utils import (
    create_insert_query_with_values,
    create_update_query_with_values,
    execute_transactional_queries,
    generate_nano_id,
)


class QuizService:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    async def _get_quiz(self, entity_id: str, quiz_id: str):
        query = (
            f"SELECT quiz_id, entity_id, class_id, section_id, title, description, status, scheduled_start "
            f"FROM {Tables.quizzes} WHERE quiz_id = :quiz_id AND entity_id = :entity_id AND active = 1;"
        )
        return await self.db.fetch_one(query, values={"quiz_id": quiz_id, "entity_id": entity_id})

    async def _count_active_questions(self, quiz_id: str) -> int:
        query = f"SELECT COUNT(1) AS count FROM {Tables.quiz_questions} WHERE quiz_id = :quiz_id AND active = 1;"
        row = await self.db.fetch_one(query, values={"quiz_id": quiz_id})
        return row["count"] if row else 0

    async def _resequence_questions(self, quiz_id: str):
        """
        Re-numbers display_order for the remaining active questions after a
        delete, so the builder UI never shows gaps like 1, 2, 4.
        """
        query = (
            f"SELECT question_id FROM {Tables.quiz_questions} "
            f"WHERE quiz_id = :quiz_id AND active = 1 ORDER BY display_order;"
        )
        rows = await self.db.fetch_all(query, values={"quiz_id": quiz_id})
        queries = [
            (
                f"UPDATE {Tables.quiz_questions} SET display_order = :display_order WHERE question_id = :question_id;",
                {"display_order": idx, "question_id": row["question_id"]},
            )
            for idx, row in enumerate(rows, start=1)
        ]
        if queries:
            await execute_transactional_queries(self.db, queries)

    async def create_quiz(self, payload: dict):
        quiz_id = generate_nano_id(length=12)
        user_id = self.x_user["user_id"]
        insert_values = {
            "quiz_id": quiz_id,
            "entity_id": payload["entity_id"],
            "class_id": payload["class_id"],
            "section_id": payload["section_id"],
            "title": payload["title"],
            "description": payload.get("description"),
            "created_by": user_id,
            "updated_by": user_id,
        }
        query, values = create_insert_query_with_values(Tables.quizzes, insert_values)

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to create quiz due to {e}")
            return False, "Failed to create quiz", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "Successfully created quiz", HTTPStatus.CREATED, {"quiz_id": quiz_id}

    async def fetch_quizzes(self, entity_id: str, class_id: str = None, section_id: str = None, status: str = None):
        where_clauses = ["q.entity_id = :entity_id", "q.active = 1"]
        values = {"entity_id": entity_id}
        if class_id:
            where_clauses.append("q.class_id = :class_id")
            values["class_id"] = class_id
        if section_id:
            where_clauses.append("q.section_id = :section_id")
            values["section_id"] = section_id
        if status:
            where_clauses.append("q.status = :status")
            values["status"] = status
        where_clause = " AND ".join(where_clauses)

        query = (
            f"SELECT q.quiz_id, q.entity_id, q.class_id, q.section_id, q.title, q.description, "
            f"q.status, q.scheduled_start, q.created_at, COUNT(qq.question_id) AS question_count "
            f"FROM {Tables.quizzes} q "
            f"LEFT JOIN {Tables.quiz_questions} qq ON qq.quiz_id = q.quiz_id AND qq.active = 1 "
            f"WHERE {where_clause} "
            f"GROUP BY q.quiz_id, q.entity_id, q.class_id, q.section_id, q.title, q.description, "
            f"q.status, q.scheduled_start, q.created_at "
            f"ORDER BY q.created_at DESC;"
        )

        try:
            rows = await self.db.fetch_all(query, values=values)
        except Exception as e:
            self.logger.error(f"failed to fetch quizzes due to {e}")
            return False, "Failed to fetch quizzes", HTTPStatus.INTERNAL_SERVER_ERROR, []

        data = [dict(row) for row in rows]
        return True, "Successfully fetched quizzes", HTTPStatus.OK, data

    async def fetch_quiz_detail(self, entity_id: str, quiz_id: str):
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND, {}

        question_query = (
            f"SELECT question_id, question_type, question_text, config, answer_key, "
            f"grading_mode, marks, display_order "
            f"FROM {Tables.quiz_questions} WHERE quiz_id = :quiz_id AND active = 1 ORDER BY display_order;"
        )
        try:
            question_rows = await self.db.fetch_all(question_query, values={"quiz_id": quiz_id})
        except Exception as e:
            self.logger.error(f"failed to fetch quiz questions due to {e}")
            return False, "Failed to fetch quiz detail", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        questions = [
            {
                "question_id": row["question_id"],
                "question_type": row["question_type"],
                "question_text": row["question_text"],
                "config": json.loads(row["config"]),
                "answer_key": json.loads(row["answer_key"]) if row["answer_key"] else None,
                "grading_mode": row["grading_mode"],
                "marks": row["marks"],
                "display_order": row["display_order"],
            }
            for row in question_rows
        ]

        data = {
            "quiz_id": quiz["quiz_id"],
            "entity_id": quiz["entity_id"],
            "class_id": quiz["class_id"],
            "section_id": quiz["section_id"],
            "title": quiz["title"],
            "description": quiz["description"],
            "status": quiz["status"],
            "scheduled_start": quiz["scheduled_start"],
            "questions": questions,
        }
        return True, "Successfully fetched quiz detail", HTTPStatus.OK, data

    async def update_quiz(self, entity_id: str, quiz_id: str, payload: dict):
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND
        if quiz["status"] != QuizStatus.draft.value:
            return False, "Only draft quizzes can be edited", HTTPStatus.BAD_REQUEST

        update_data = {"updated_by": self.x_user["user_id"]}
        if payload.get("title") is not None:
            update_data["title"] = payload["title"]
        if payload.get("description") is not None:
            update_data["description"] = payload["description"]

        where_condition = {"quiz_id": quiz_id, "entity_id": entity_id}
        query, values = create_update_query_with_values(Tables.quizzes, update_data, where_condition)

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to update quiz due to {e}")
            return False, "Failed to update quiz", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully updated quiz", HTTPStatus.OK

    async def delete_quiz(self, entity_id: str, quiz_id: str):
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND
        if quiz["status"] != QuizStatus.draft.value:
            return False, "Only draft quizzes can be deleted", HTTPStatus.BAD_REQUEST

        user_id = self.x_user["user_id"]
        queries = [
            (
                f"UPDATE {Tables.quizzes} SET active = 0, updated_by = :updated_by "
                f"WHERE quiz_id = :quiz_id AND entity_id = :entity_id;",
                {"updated_by": user_id, "quiz_id": quiz_id, "entity_id": entity_id},
            ),
            (
                f"UPDATE {Tables.quiz_questions} SET active = 0, updated_by = :updated_by "
                f"WHERE quiz_id = :quiz_id AND entity_id = :entity_id;",
                {"updated_by": user_id, "quiz_id": quiz_id, "entity_id": entity_id},
            ),
        ]

        try:
            await execute_transactional_queries(self.db, queries)
        except Exception as e:
            self.logger.error(f"failed to delete quiz due to {e}")
            return False, "Failed to delete quiz", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully deleted quiz", HTTPStatus.OK

    async def add_question(self, entity_id: str, quiz_id: str, payload: dict):
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND, {}
        if quiz["status"] != QuizStatus.draft.value:
            return False, "Cannot add questions once a quiz is marked ready or published", HTTPStatus.BAD_REQUEST, {}

        question_count = await self._count_active_questions(quiz_id)
        if question_count >= QUIZ_MAX_QUESTIONS:
            return (
                False,
                f"A quiz cannot have more than {QUIZ_MAX_QUESTIONS} questions",
                HTTPStatus.BAD_REQUEST,
                {},
            )

        question_id = generate_nano_id(length=12)
        user_id = self.x_user["user_id"]
        insert_values = {
            "question_id": question_id,
            "quiz_id": quiz_id,
            "entity_id": entity_id,
            "question_type": payload["question_type"],
            "question_text": payload["question_text"],
            "config": json.dumps(payload.get("config") or {}),
            "answer_key": json.dumps(payload["answer_key"]) if payload.get("answer_key") is not None else None,
            "grading_mode": payload["grading_mode"],
            "marks": payload.get("marks", 1),
            "display_order": question_count + 1,
            "created_by": user_id,
            "updated_by": user_id,
        }
        query, values = create_insert_query_with_values(Tables.quiz_questions, insert_values)

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to add question due to {e}")
            return False, "Failed to add question", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "Successfully added question", HTTPStatus.CREATED, {"question_id": question_id}

    async def update_question(self, entity_id: str, quiz_id: str, question_id: str, payload: dict):
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND
        if quiz["status"] != QuizStatus.draft.value:
            return False, "Cannot edit questions once a quiz is marked ready or published", HTTPStatus.BAD_REQUEST

        update_data = {
            "question_type": payload["question_type"],
            "question_text": payload["question_text"],
            "config": json.dumps(payload.get("config") or {}),
            "answer_key": json.dumps(payload["answer_key"]) if payload.get("answer_key") is not None else None,
            "grading_mode": payload["grading_mode"],
            "marks": payload.get("marks", 1),
            "updated_by": self.x_user["user_id"],
        }
        where_condition = {"question_id": question_id, "quiz_id": quiz_id, "entity_id": entity_id}
        query, values = create_update_query_with_values(Tables.quiz_questions, update_data, where_condition)

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to update question due to {e}")
            return False, "Failed to update question", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully updated question", HTTPStatus.OK

    async def delete_question(self, entity_id: str, quiz_id: str, question_id: str):
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND
        if quiz["status"] != QuizStatus.draft.value:
            return False, "Cannot delete questions once a quiz is marked ready or published", HTTPStatus.BAD_REQUEST

        query = (
            f"UPDATE {Tables.quiz_questions} SET active = 0, updated_by = :updated_by "
            f"WHERE question_id = :question_id AND quiz_id = :quiz_id AND entity_id = :entity_id;"
        )
        values = {
            "updated_by": self.x_user["user_id"],
            "question_id": question_id,
            "quiz_id": quiz_id,
            "entity_id": entity_id,
        }

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to delete question due to {e}")
            return False, "Failed to delete question", HTTPStatus.INTERNAL_SERVER_ERROR

        await self._resequence_questions(quiz_id)

        return True, "Successfully deleted question", HTTPStatus.OK

    async def mark_quiz_ready(self, entity_id: str, quiz_id: str):
        """
        "Save" action: locks question editing (same as published) but stops
        short of scheduling/going live. A ready quiz can still be moved back
        to draft, unlike a published one.
        """
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND
        if quiz["status"] != QuizStatus.draft.value:
            return False, "Only draft quizzes can be marked ready", HTTPStatus.BAD_REQUEST

        question_count = await self._count_active_questions(quiz_id)
        if not (QUIZ_MIN_QUESTIONS <= question_count <= QUIZ_MAX_QUESTIONS):
            return (
                False,
                f"A quiz needs between {QUIZ_MIN_QUESTIONS} and {QUIZ_MAX_QUESTIONS} questions before "
                f"it can be marked ready (currently has {question_count})",
                HTTPStatus.BAD_REQUEST,
            )

        query = (
            f"UPDATE {Tables.quizzes} SET status = :status, updated_by = :updated_by "
            f"WHERE quiz_id = :quiz_id AND entity_id = :entity_id;"
        )
        values = {
            "status": QuizStatus.ready.value,
            "updated_by": self.x_user["user_id"],
            "quiz_id": quiz_id,
            "entity_id": entity_id,
        }

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to mark quiz ready due to {e}")
            return False, "Failed to mark quiz ready", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Quiz marked ready to publish", HTTPStatus.OK

    async def revert_quiz_to_draft(self, entity_id: str, quiz_id: str):
        """Moves a "ready" quiz back to draft so its questions can be edited again."""
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND
        if quiz["status"] != QuizStatus.ready.value:
            return False, "Only quizzes marked ready can be moved back to draft", HTTPStatus.BAD_REQUEST

        query = (
            f"UPDATE {Tables.quizzes} SET status = :status, updated_by = :updated_by "
            f"WHERE quiz_id = :quiz_id AND entity_id = :entity_id;"
        )
        values = {
            "status": QuizStatus.draft.value,
            "updated_by": self.x_user["user_id"],
            "quiz_id": quiz_id,
            "entity_id": entity_id,
        }

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to revert quiz to draft due to {e}")
            return False, "Failed to move quiz back to draft", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Quiz moved back to draft", HTTPStatus.OK

    async def publish_quiz(self, entity_id: str, quiz_id: str, scheduled_start):
        quiz = await self._get_quiz(entity_id, quiz_id)
        if not quiz:
            return False, "Quiz not found", HTTPStatus.NOT_FOUND
        if quiz["status"] == QuizStatus.published.value:
            return False, "Quiz is already published", HTTPStatus.BAD_REQUEST
        if quiz["status"] != QuizStatus.ready.value:
            return False, "Save the quiz as ready before publishing it", HTTPStatus.BAD_REQUEST

        query = (
            f"UPDATE {Tables.quizzes} SET status = :status, scheduled_start = :scheduled_start, "
            f"updated_by = :updated_by WHERE quiz_id = :quiz_id AND entity_id = :entity_id;"
        )
        values = {
            "status": QuizStatus.published.value,
            "scheduled_start": scheduled_start,
            "updated_by": self.x_user["user_id"],
            "quiz_id": quiz_id,
            "entity_id": entity_id,
        }

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to publish quiz due to {e}")
            return False, "Failed to publish quiz", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully published quiz", HTTPStatus.OK
