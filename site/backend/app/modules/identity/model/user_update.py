from pydantic import BaseModel, Field


class UserUpdateMe(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
