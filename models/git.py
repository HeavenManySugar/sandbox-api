from pydantic import BaseModel, HttpUrl


class GitUrl(BaseModel):
    url: HttpUrl
