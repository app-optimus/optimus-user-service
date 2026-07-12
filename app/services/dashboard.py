from http import HTTPStatus

from app.enums import QuizStatus, Tables, UserRoles


class DashboardService:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    async def fetch_student_counts_by_class_section(self, entity_id: str):
        """
        Returns, per active class in the given school, the list of active
        sections along with how many active students are assigned to each
        one. Classes with no sections yet are still returned (with an empty
        `sections` list) so the UI can surface that gap.
        """
        query = f"""
        SELECT
            c.class_id AS class_id,
            c.class_name AS class_name,
            c.display_order AS class_display_order,
            s.section_id AS section_id,
            s.section_name AS section_name,
            s.display_order AS section_display_order,
            COUNT(ued.user_id) AS student_count
        FROM {Tables.entity_classes} c
        LEFT JOIN {Tables.entity_class_sections} s
            ON s.class_id = c.class_id AND s.active = 1
        LEFT JOIN {Tables.user_entity_details} ued
            ON ued.class_id = c.class_id
            AND ued.section_id = s.section_id
            AND ued.entity_id = c.entity_id
            AND ued.active = 1
            AND ued.user_role = :student_role
        WHERE c.entity_id = :entity_id AND c.active = 1
        GROUP BY c.class_id, c.class_name, c.display_order, s.section_id, s.section_name, s.display_order
        ORDER BY c.display_order, s.display_order;
        """

        try:
            rows = await self.db.fetch_all(
                query, values={"entity_id": entity_id, "student_role": UserRoles.student.value}
            )
        except Exception as e:
            self.logger.error(f"failed to fetch student counts by section due to {e}")
            return False, "Failed to fetch student counts", HTTPStatus.INTERNAL_SERVER_ERROR, []

        classes_by_id = {}
        ordered_class_ids = []
        for row in rows:
            class_id = row["class_id"]
            if class_id not in classes_by_id:
                classes_by_id[class_id] = {
                    "class_id": class_id,
                    "class_name": row["class_name"],
                    "sections": [],
                }
                ordered_class_ids.append(class_id)

            if row["section_id"]:
                classes_by_id[class_id]["sections"].append({
                    "section_id": row["section_id"],
                    "section_name": row["section_name"],
                    "student_count": row["student_count"] or 0,
                })

        data = [classes_by_id[class_id] for class_id in ordered_class_ids]
        return True, "Successfully fetched student counts", HTTPStatus.OK, data

    async def fetch_headcount_summary(self, entity_id: str):
        """
        Returns the total number of active students and the total number of
        active teaching staff (teachers + principal) for the given school.
        """
        query = f"""
        SELECT
            SUM(CASE WHEN user_role = :student_role THEN 1 ELSE 0 END) AS student_count,
            SUM(CASE WHEN user_role IN (:teacher_role, :principal_role) THEN 1 ELSE 0 END) AS teacher_count
        FROM {Tables.user_entity_details}
        WHERE entity_id = :entity_id AND active = 1;
        """

        try:
            row = await self.db.fetch_one(
                query,
                values={
                    "entity_id": entity_id,
                    "student_role": UserRoles.student.value,
                    "teacher_role": UserRoles.teacher.value,
                    "principal_role": UserRoles.principal.value,
                },
            )
        except Exception as e:
            self.logger.error(f"failed to fetch headcount summary due to {e}")
            return False, "Failed to fetch headcount summary", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        data = {
            "student_count": (row["student_count"] if row and row["student_count"] else 0),
            "teacher_count": (row["teacher_count"] if row and row["teacher_count"] else 0),
        }
        return True, "Successfully fetched headcount summary", HTTPStatus.OK, data

    async def fetch_quiz_summary(self, entity_id: str):
        """
        Returns the total number of active draft, ready, and published
        quizzes for the given school.
        """
        query = f"""
        SELECT
            SUM(CASE WHEN status = :draft_status THEN 1 ELSE 0 END) AS draft_count,
            SUM(CASE WHEN status = :ready_status THEN 1 ELSE 0 END) AS ready_count,
            SUM(CASE WHEN status = :published_status THEN 1 ELSE 0 END) AS published_count
        FROM {Tables.quizzes}
        WHERE entity_id = :entity_id AND active = 1;
        """

        try:
            row = await self.db.fetch_one(
                query,
                values={
                    "entity_id": entity_id,
                    "draft_status": QuizStatus.draft.value,
                    "ready_status": QuizStatus.ready.value,
                    "published_status": QuizStatus.published.value,
                },
            )
        except Exception as e:
            self.logger.error(f"failed to fetch quiz summary due to {e}")
            return False, "Failed to fetch quiz summary", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        data = {
            "draft_count": (row["draft_count"] if row and row["draft_count"] else 0),
            "ready_count": (row["ready_count"] if row and row["ready_count"] else 0),
            "published_count": (row["published_count"] if row and row["published_count"] else 0),
        }
        return True, "Successfully fetched quiz summary", HTTPStatus.OK, data
