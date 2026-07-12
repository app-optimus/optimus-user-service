import os
from pathlib import Path

import aiofiles

from app.settings import STUDY_MATERIALS_STORAGE_DIR


class LocalFileStorage:
    """
    Minimal file storage backed by local disk. A future cloud-backed
    implementation (e.g. an S3FileStorage) should expose the same three
    methods - save/resolve/delete - so callers never need to change when
    storage is swapped out.
    """

    def __init__(self, root_dir: str = STUDY_MATERIALS_STORAGE_DIR):
        self.root_dir = Path(root_dir)

    async def save(self, entity_id: str, material_id: str, filename: str, content: bytes) -> str:
        """Writes `content` to disk and returns the path relative to root_dir."""
        safe_name = os.path.basename(filename)
        relative_path = os.path.join(entity_id, f"{material_id}_{safe_name}")
        absolute_path = self.root_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(absolute_path, "wb") as f:
            await f.write(content)

        return relative_path

    def resolve(self, relative_path: str) -> str:
        """Returns the absolute filesystem path for a previously stored relative path."""
        return str(self.root_dir / relative_path)

    def delete(self, relative_path: str) -> None:
        absolute_path = self.root_dir / relative_path
        if absolute_path.exists():
            absolute_path.unlink()
