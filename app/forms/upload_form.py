import os
import shutil
from fastapi import Request


class UploadClassificationForm:
    def __init__(self, request: Request) -> None:
        self.request: Request = request
        self.errors: list = []
        self.image_id: str = ""
        self.model_id: str = ""

    async def load_data(self):
        form = await self.request.form()
        image = form.get("uploadImage")
        self.image_id = image.filename
        shutil.rmtree("app/static/uploads")
        os.makedirs("app/static/uploads", exist_ok=True)
        with open("app/static/uploads/" + self.image_id, "wb") as f:
            shutil.copyfileobj(image.file, f)

        self.model_id = form.get("model_id")

    def is_valid(self):
        if not self.image_id or not isinstance(self.image_id, str):
            self.errors.append("A valid image id is required")
        if not self.model_id or not isinstance(self.model_id, str):
            self.errors.append("A valid model id is required")
        if not self.errors:
            return True
        return False
