from uuid import UUID
from pydantic import BaseModel, Field

class ReadmeGenerateRequest(BaseModel):
    project_id: UUID

    language: str = Field(
        default="es",
        pattern="^(es|en)$",
        description="Idioma del README generado",
    )

class ReadmeSourceResponse(BaseModel):
    path: str
    language: str

class ReadmeGenerateResponse(BaseModel):
    content: str
    sources: list[ReadmeSourceResponse]