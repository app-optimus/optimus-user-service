from http import HTTPStatus

from pymysql import IntegrityError

from app.enums import Tables
from app.utils import (
    create_query_params,
    generate_nano_id,
    create_insert_query_with_values,
    create_update_query_with_values,
    where_clause_for_multiple,
)


class SubjectService:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    async def fetch_subjects(self, entity_id: str, class_id: str = None):
        _where = {
            "entity_id = '%s'": entity_id,
            "active = %s": True,
        }
        if class_id:
            _where["class_id = '%s'"] = class_id

        _columns, _where = create_query_params(
            columns=["subject_id", "class_id", "subject_name", "display_order"], where_dict=_where
        )
        query = f"SELECT {_columns} FROM {Tables.subjects} WHERE {_where} ORDER BY class_id, display_order;"

        try:
            rows = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch subjects due to {e}")
            return False, "Failed to fetch subjects", HTTPStatus.INTERNAL_SERVER_ERROR, []

        data = [dict(row) for row in rows]
        return True, "Successfully fetched subjects", HTTPStatus.OK, data

    async def _get_next_order(self, class_id: str) -> int:
        query = (
            f"SELECT COALESCE(MAX(display_order), 0) AS max_order "
            f"FROM {Tables.subjects} WHERE class_id = :class_id AND active = 1;"
        )
        row = await self.db.fetch_one(query, values={"class_id": class_id})
        return (row["max_order"] + 1) if row else 1

    async def create_subject(self, entity_id: str, class_id: str, subject_name: str):
        next_order = await self._get_next_order(class_id)
        user_id = self.x_user["user_id"]
        subject_data = {
            "subject_id": generate_nano_id(length=12),
            "entity_id": entity_id,
            "class_id": class_id,
            "subject_name": subject_name,
            "display_order": next_order,
            "created_by": user_id,
            "updated_by": user_id,
        }
        query, values = create_insert_query_with_values(Tables.subjects, subject_data)

        try:
            await self.db.execute(query=query, values=values)
        except IntegrityError:
            return False, "Subject with this name already exists in this class", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to create subject due to {e}")
            return False, "Failed to create subject", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully created subject", HTTPStatus.CREATED

    async def rename_subject(self, entity_id: str, class_id: str, subject_id: str, subject_name: str):
        update_data = {"subject_name": subject_name, "updated_by": self.x_user["user_id"]}
        where_condition = {"subject_id": subject_id, "class_id": class_id, "entity_id": entity_id}
        query, values = create_update_query_with_values(Tables.subjects, update_data, where_condition)

        try:
            await self.db.execute(query=query, values=values)
        except IntegrityError:
            return False, "Subject with this name already exists in this class", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to rename subject due to {e}")
            return False, "Failed to rename subject", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully renamed subject", HTTPStatus.OK

    async def delete_subjects(self, entity_id: str, class_id: str, subject_ids: list):
        user_id = self.x_user["user_id"]
        subject_where = where_clause_for_multiple("subject_id", subject_ids)
        query = (
            f"UPDATE {Tables.subjects} SET active = 0, updated_by = :updated_by "
            f"WHERE {subject_where} AND class_id = :class_id AND entity_id = :entity_id AND active = 1;"
        )
        values = {"updated_by": user_id, "class_id": class_id, "entity_id": entity_id}

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to delete subjects due to {e}")
            return False, "Failed to delete subjects", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully deleted subjects", HTTPStatus.OK
