from __future__ import annotations
import uuid
from datetime import date
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, field_validator


def generate_id(entry_type: str) -> str:
    prefix = {"solution": "sol", "tip": "tip"}[entry_type]
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class Solution(BaseModel):
    id: str = ""
    type: Literal["solution"] = "solution"
    title: str
    problem: str
    solution: str
    tags: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    contributor: str = "anonymous"
    created: str = Field(default_factory=lambda: str(date.today()))
    votes: int = 0

    def model_post_init(self, __context):
        if not self.id:
            self.id = generate_id("solution")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v

    @field_validator("problem")
    @classmethod
    def problem_not_empty(cls, v):
        if not v.strip():
            raise ValueError("problem cannot be empty")
        return v

    @field_validator("solution")
    @classmethod
    def solution_not_empty(cls, v):
        if not v.strip():
            raise ValueError("solution cannot be empty")
        return v

    def to_yaml(self) -> str:
        return yaml.dump(self.model_dump(), default_flow_style=False, sort_keys=False)


class Tip(BaseModel):
    id: str = ""
    type: Literal["tip"] = "tip"
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    contributor: str = "anonymous"
    created: str = Field(default_factory=lambda: str(date.today()))
    votes: int = 0

    def model_post_init(self, __context):
        if not self.id:
            self.id = generate_id("tip")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v

    def to_yaml(self) -> str:
        return yaml.dump(self.model_dump(), default_flow_style=False, sort_keys=False)


def load_entry(path: Path) -> Solution | Tip:
    data = yaml.safe_load(path.read_text())
    if data["type"] == "solution":
        return Solution(**data)
    elif data["type"] == "tip":
        return Tip(**data)
    raise ValueError(f"Unknown entry type: {data.get('type')}")


def validate_entry(data: dict) -> Solution | Tip:
    entry_type = data.get("type", "solution")
    if entry_type == "solution":
        return Solution(**data)
    elif entry_type == "tip":
        return Tip(**data)
    raise ValueError(f"Unknown entry type: {entry_type}")
