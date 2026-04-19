from http import HTTPStatus
from collections import defaultdict

from pymysql import IntegrityError

from app.enums import Tables
from app.utils import (
    create_query_params,
    generate_nano_id,
    create_insert_query_with_values,
    create_update_query_with_values,
    execute_transactional_queries,
    where_clause_for_multiple,
)


class ClassStructureService:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user

    async def fetch_class_structure(self, entity_id: str):
        _columns = ["class_id", "class_name", "display_order"]
        _where = {
            "entity_id = '%s'": entity_id,
            "active = %s": True,
        }
        _columns, _where = create_query_params(columns=_columns, where_dict=_where)
        class_query = f"SELECT {_columns} FROM {Tables.entity_classes} WHERE {_where} ORDER BY display_order;"

        try:
            class_rows = await self.db.fetch_all(class_query)
        except Exception as e:
            self.logger.error(f"failed to fetch class structure due to {e}")
            return False, "Failed to fetch class structure", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        if not class_rows:
            return True, "Successfully fetched class structure", HTTPStatus.OK, []

        class_ids = [row["class_id"] for row in class_rows]
        section_where = where_clause_for_multiple("class_id", class_ids)
        section_query = (
            f"SELECT section_id, class_id, section_name, display_order "
            f"FROM {Tables.entity_class_sections} "
            f"WHERE {section_where} AND active = 1 "
            f"ORDER BY display_order;"
        )

        try:
            section_rows = await self.db.fetch_all(section_query)
        except Exception as e:
            self.logger.error(f"failed to fetch sections due to {e}")
            return False, "Failed to fetch class structure", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        sections_by_class = defaultdict(list)
        for row in section_rows:
            sections_by_class[row["class_id"]].append({
                "section_id": row["section_id"],
                "section_name": row["section_name"],
                "display_order": row["display_order"],
            })

        data = []
        for row in class_rows:
            data.append({
                "class_id": row["class_id"],
                "class_name": row["class_name"],
                "display_order": row["display_order"],
                "sections": sections_by_class.get(row["class_id"], []),
            })

        return True, "Successfully fetched class structure", HTTPStatus.OK, data

    async def _get_next_class_order(self, entity_id: str) -> int:
        query = (
            f"SELECT COALESCE(MAX(display_order), 0) AS max_order "
            f"FROM {Tables.entity_classes} "
            f"WHERE entity_id = :entity_id AND active = 1;"
        )
        row = await self.db.fetch_one(query, values={"entity_id": entity_id})
        return (row["max_order"] + 1) if row else 1

    async def _get_next_section_order(self, class_id: str) -> int:
        query = (
            f"SELECT COALESCE(MAX(display_order), 0) AS max_order "
            f"FROM {Tables.entity_class_sections} "
            f"WHERE class_id = :class_id AND active = 1;"
        )
        row = await self.db.fetch_one(query, values={"class_id": class_id})
        return (row["max_order"] + 1) if row else 1

    async def create_class(self, payload: dict):
        entity_id = payload["entity_id"]
        class_name = payload["class_name"]
        sections = payload.get("sections") or []

        next_order = await self._get_next_class_order(entity_id)
        class_id = generate_nano_id(length=12)
        user_id = self.x_user["user_id"]

        queries = []

        class_data = {
            "class_id": class_id,
            "entity_id": entity_id,
            "class_name": class_name,
            "display_order": next_order,
            "created_by": user_id,
            "updated_by": user_id,
        }
        queries.append(create_insert_query_with_values(Tables.entity_classes, class_data))

        for idx, section in enumerate(sections):
            section_data = {
                "section_id": generate_nano_id(length=12),
                "class_id": class_id,
                "entity_id": entity_id,
                "section_name": section["section_name"],
                "display_order": idx + 1,
                "created_by": user_id,
                "updated_by": user_id,
            }
            queries.append(create_insert_query_with_values(Tables.entity_class_sections, section_data))

        try:
            await execute_transactional_queries(self.db, queries)
        except IntegrityError:
            return False, "Class with this name already exists in this school", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to create class due to {e}")
            return False, "Failed to create class", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully created class", HTTPStatus.CREATED

    async def bulk_create_classes(self, entity_id: str, classes: list):
        next_order = await self._get_next_class_order(entity_id)
        user_id = self.x_user["user_id"]
        queries = []

        for class_idx, cls in enumerate(classes):
            class_id = generate_nano_id(length=12)
            class_data = {
                "class_id": class_id,
                "entity_id": entity_id,
                "class_name": cls["class_name"],
                "display_order": next_order + class_idx,
                "created_by": user_id,
                "updated_by": user_id,
            }
            queries.append(create_insert_query_with_values(Tables.entity_classes, class_data))

            sections = cls.get("sections") or []
            for sec_idx, section in enumerate(sections):
                section_data = {
                    "section_id": generate_nano_id(length=12),
                    "class_id": class_id,
                    "entity_id": entity_id,
                    "section_name": section["section_name"],
                    "display_order": sec_idx + 1,
                    "created_by": user_id,
                    "updated_by": user_id,
                }
                queries.append(create_insert_query_with_values(Tables.entity_class_sections, section_data))

        try:
            await execute_transactional_queries(self.db, queries)
        except IntegrityError:
            return False, "One or more class names already exist in this school", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to bulk create classes due to {e}")
            return False, "Failed to bulk create classes", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully created classes", HTTPStatus.CREATED

    async def rename_class(self, entity_id: str, class_id: str, class_name: str):
        update_data = {"class_name": class_name, "updated_by": self.x_user["user_id"]}
        where_condition = {"class_id": class_id, "entity_id": entity_id}
        query, values = create_update_query_with_values(Tables.entity_classes, update_data, where_condition)

        try:
            await self.db.execute(query=query, values=values)
        except IntegrityError:
            return False, "Class with this name already exists in this school", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to rename class due to {e}")
            return False, "Failed to rename class", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully renamed class", HTTPStatus.OK

    async def delete_classes(self, entity_id: str, class_ids: list):
        user_id = self.x_user["user_id"]
        queries = []

        class_where = where_clause_for_multiple("class_id", class_ids)
        deactivate_classes_query = (
            f"UPDATE {Tables.entity_classes} SET active = 0, updated_by = :updated_by "
            f"WHERE {class_where} AND entity_id = :entity_id AND active = 1;"
        )
        queries.append((deactivate_classes_query, {"updated_by": user_id, "entity_id": entity_id}))

        deactivate_sections_query = (
            f"UPDATE {Tables.entity_class_sections} SET active = 0, updated_by = :updated_by "
            f"WHERE {class_where} AND entity_id = :entity_id AND active = 1;"
        )
        queries.append((deactivate_sections_query, {"updated_by": user_id, "entity_id": entity_id}))

        try:
            await execute_transactional_queries(self.db, queries)
        except Exception as e:
            self.logger.error(f"failed to delete classes due to {e}")
            return False, "Failed to delete classes", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully deleted classes", HTTPStatus.OK

    async def add_sections(self, entity_id: str, class_id: str, sections: list):
        next_order = await self._get_next_section_order(class_id)
        user_id = self.x_user["user_id"]
        queries = []

        for idx, section in enumerate(sections):
            section_data = {
                "section_id": generate_nano_id(length=12),
                "class_id": class_id,
                "entity_id": entity_id,
                "section_name": section["section_name"],
                "display_order": next_order + idx,
                "created_by": user_id,
                "updated_by": user_id,
            }
            queries.append(create_insert_query_with_values(Tables.entity_class_sections, section_data))

        try:
            await execute_transactional_queries(self.db, queries)
        except IntegrityError:
            return False, "One or more section names already exist in this class", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to add sections due to {e}")
            return False, "Failed to add sections", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully added sections", HTTPStatus.CREATED

    async def rename_section(self, entity_id: str, class_id: str, section_id: str, section_name: str):
        update_data = {"section_name": section_name, "updated_by": self.x_user["user_id"]}
        where_condition = {"section_id": section_id, "class_id": class_id, "entity_id": entity_id}
        query, values = create_update_query_with_values(Tables.entity_class_sections, update_data, where_condition)

        try:
            await self.db.execute(query=query, values=values)
        except IntegrityError:
            return False, "Section with this name already exists in this class", HTTPStatus.BAD_REQUEST
        except Exception as e:
            self.logger.error(f"failed to rename section due to {e}")
            return False, "Failed to rename section", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully renamed section", HTTPStatus.OK

    async def delete_sections(self, entity_id: str, class_id: str, section_ids: list):
        user_id = self.x_user["user_id"]
        section_where = where_clause_for_multiple("section_id", section_ids)
        query = (
            f"UPDATE {Tables.entity_class_sections} SET active = 0, updated_by = :updated_by "
            f"WHERE {section_where} AND class_id = :class_id AND entity_id = :entity_id AND active = 1;"
        )
        values = {"updated_by": user_id, "class_id": class_id, "entity_id": entity_id}

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to delete sections due to {e}")
            return False, "Failed to delete sections", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully deleted sections", HTTPStatus.OK
