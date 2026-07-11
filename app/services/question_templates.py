import json
from http import HTTPStatus

from app.enums import Tables


class QuestionTemplateService:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    async def fetch_question_templates(self):
        """
        Returns every active question template, ordered for display. This is
        the global catalog of question types a quiz question can be built
        from - not tied to any school.
        """
        query = (
            f"SELECT template_id, template_code, template_name, description, "
            f"default_grading_mode, config_schema, sample_question, display_order "
            f"FROM {Tables.question_templates} "
            f"WHERE active = 1 "
            f"ORDER BY display_order;"
        )

        try:
            rows = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch question templates due to {e}")
            return False, "Failed to fetch question templates", HTTPStatus.INTERNAL_SERVER_ERROR, []

        data = []
        for row in rows:
            data.append({
                "template_id": row["template_id"],
                "template_code": row["template_code"],
                "template_name": row["template_name"],
                "description": row["description"],
                "default_grading_mode": row["default_grading_mode"],
                "config_schema": json.loads(row["config_schema"]),
                "sample_question": json.loads(row["sample_question"]),
                "display_order": row["display_order"],
            })

        return True, "Successfully fetched question templates", HTTPStatus.OK, data
