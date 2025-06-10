import os
import uuid
import shutil
import asyncio
from fastapi import Request


class UploadClassificationForm:
    def __init__(self, request: Request) -> None:
        self.request: Request = request
        self.errors: list = []
        self.image_id: str = ""
        self.model_id: str = ""
        self.upload_dir: str = ""

    async def load_data(self):
        form = await self.request.form()
        image = form.get("uploadImage")
        self.image_id = image.filename
        self.model_id = form.get("model_id")

        unique_folder = str(uuid.uuid4())
        self.upload_dir = os.path.join("app/static", unique_folder)
        os.makedirs(self.upload_dir, exist_ok=True)

        image_path = os.path.join(self.upload_dir, self.image_id)
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)

    def is_valid(self):
        if not self.image_id or not isinstance(self.image_id, str):
            self.errors.append("A valid image id is required")
        if not self.model_id or not isinstance(self.model_id, str):
            self.errors.append("A valid model id is required")
        if not self.errors:
            return True
        return False


async def delete_folder(path: str):
    await asyncio.sleep(5)
    if os.path.exists(path):
        shutil.rmtree(path)
