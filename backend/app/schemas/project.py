from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del proyecto",
    )
    description: str | None = Field(
        default=None,
        description="Descripción opcional del proyecto",
    )


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: UUID
    status: str
    uploaded_file: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)