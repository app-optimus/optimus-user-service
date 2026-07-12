import os
from http import HTTPStatus

from fastapi import UploadFile

from app.enums import STUDY_MATERIAL_ALLOWED_EXTENSIONS, STUDY_MATERIAL_MAX_FILE_SIZE_MB, Tables
from app.services.storage import LocalFileStorage
from app.utils import create_query_params, generate_nano_id, create_insert_query_with_values


class StudyMaterialService:

    def __init__(self, db=None, logger=None, x_user=None):
        self.db = db
        self.logger = logger
        self.x_user = x_user
        self.storage = LocalFileStorage()

    async def upload_material(
        self, entity_id: str, class_id: str, section_id: str, subject_id: str,
        material_type: str, title: str, description: str, file: UploadFile,
    ):
        extension = os.path.splitext(file.filename or "")[1].lower()
        if extension not in STUDY_MATERIAL_ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(STUDY_MATERIAL_ALLOWED_EXTENSIONS))
            return False, f"Unsupported file type. Allowed extensions: {allowed}", HTTPStatus.BAD_REQUEST, {}

        content = await file.read()
        max_size_bytes = STUDY_MATERIAL_MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_size_bytes:
            return (
                False,
                f"File is too large. Maximum allowed size is {STUDY_MATERIAL_MAX_FILE_SIZE_MB}MB",
                HTTPStatus.BAD_REQUEST,
                {},
            )
        if not content:
            return False, "Uploaded file is empty", HTTPStatus.BAD_REQUEST, {}

        material_id = generate_nano_id(length=12)
        try:
            relative_path = await self.storage.save(entity_id, material_id, file.filename, content)
        except Exception as e:
            self.logger.error(f"failed to save study material file due to {e}")
            return False, "Failed to store uploaded file", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        user_id = self.x_user["user_id"]
        material_data = {
            "material_id": material_id,
            "entity_id": entity_id,
            "class_id": class_id,
            "section_id": section_id,
            "subject_id": subject_id,
            "material_type": material_type,
            "title": title,
            "description": description,
            "file_name": file.filename,
            "file_path": relative_path,
            "file_size": len(content),
            "mime_type": file.content_type or "application/octet-stream",
            "created_by": user_id,
            "updated_by": user_id,
        }
        query, values = create_insert_query_with_values(Tables.study_materials, material_data)

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to insert study material due to {e}")
            self.storage.delete(relative_path)
            return False, "Failed to save study material", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        return True, "Successfully uploaded study material", HTTPStatus.CREATED, {"material_id": material_id}

    async def fetch_materials(
        self, entity_id: str, class_id: str = None, section_id: str = None,
        subject_id: str = None, material_type: str = None,
    ):
        _columns = [
            "sm.material_id", "sm.class_id", "ec.class_name", "sm.section_id", "ecs.section_name",
            "sm.subject_id", "s.subject_name", "sm.material_type", "sm.title", "sm.description",
            "sm.file_name", "sm.file_size", "sm.mime_type", "sm.created_by", "sm.created_at",
        ]
        _where = {
            "sm.entity_id = '%s'": entity_id,
            "sm.active = %s": True,
        }
        if class_id:
            _where["sm.class_id = '%s'"] = class_id
        if section_id:
            _where["sm.section_id = '%s'"] = section_id
        if subject_id:
            _where["sm.subject_id = '%s'"] = subject_id
        if material_type:
            _where["sm.material_type = '%s'"] = material_type

        _columns, _where = create_query_params(columns=_columns, where_dict=_where)

        query = (
            f"SELECT {_columns} FROM {Tables.study_materials} sm "
            f"JOIN {Tables.entity_classes} ec ON sm.class_id = ec.class_id "
            f"LEFT JOIN {Tables.entity_class_sections} ecs ON sm.section_id = ecs.section_id "
            f"JOIN {Tables.subjects} s ON sm.subject_id = s.subject_id "
            f"WHERE {_where} ORDER BY sm.created_at DESC;"
        )

        try:
            response = await self.db.fetch_all(query)
        except Exception as e:
            self.logger.error(f"failed to fetch study materials due to {e}")
            return False, "Failed to fetch study materials", HTTPStatus.INTERNAL_SERVER_ERROR, []

        data = [dict(row) for row in response]
        return True, "Successfully fetched study materials", HTTPStatus.OK, data

    async def get_material_for_download(self, entity_id: str, material_id: str):
        query = (
            f"SELECT file_path, file_name, mime_type FROM {Tables.study_materials} "
            f"WHERE material_id = :material_id AND entity_id = :entity_id AND active = 1;"
        )
        try:
            row = await self.db.fetch_one(query, values={"material_id": material_id, "entity_id": entity_id})
        except Exception as e:
            self.logger.error(f"failed to fetch study material for download due to {e}")
            return False, "Failed to fetch study material", HTTPStatus.INTERNAL_SERVER_ERROR, {}

        if not row:
            return False, "Study material not found", HTTPStatus.NOT_FOUND, {}

        absolute_path = self.storage.resolve(row["file_path"])
        if not os.path.exists(absolute_path):
            return False, "Study material file is missing on the server", HTTPStatus.NOT_FOUND, {}

        return True, "Successfully fetched study material", HTTPStatus.OK, {
            "absolute_path": absolute_path,
            "file_name": row["file_name"],
            "mime_type": row["mime_type"],
        }

    async def delete_material(self, entity_id: str, material_id: str):
        query = (
            f"UPDATE {Tables.study_materials} SET active = 0, updated_by = :updated_by "
            f"WHERE material_id = :material_id AND entity_id = :entity_id AND active = 1;"
        )
        values = {"updated_by": self.x_user["user_id"], "material_id": material_id, "entity_id": entity_id}

        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            self.logger.error(f"failed to delete study material due to {e}")
            return False, "Failed to delete study material", HTTPStatus.INTERNAL_SERVER_ERROR

        return True, "Successfully deleted study material", HTTPStatus.OK
