import uuid

from pydantic import BaseModel, HttpUrl


class GitUrl(BaseModel):
    url: HttpUrl


class submission(GitUrl):
    uuid: uuid.UUID
