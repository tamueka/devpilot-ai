from uuid import UUID

from pydantic import BaseModel, Field


class UnitTestGenerateRequest(BaseModel):
    project_id: UUID
    document_id: UUID

    framework: str | None = Field(
        default=None,
        max_length=50,
        description=(
            "Framework de testing opcional. "
            "Si no se indica, DevPilot intentará detectarlo."
        ),
    )


class UnitTestSourceResponse(BaseModel):
    path: str
    language: str


class UnitTestGenerateResponse(BaseModel):
    content: str
    suggested_filename: str
    sources: list[UnitTestSourceResponse]