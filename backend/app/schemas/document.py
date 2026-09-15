from uuid import UUID
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    path: str
    filename: str
    extension: str
    language: str
    size: int

    model_config = ConfigDict(
        from_attributes=True,
    )