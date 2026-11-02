from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import IngestionStatus, TriggerType
from app.schemas.common import SourceRef


class IngestionRequest(BaseModel):
    source_id: int = Field(gt=0)


class RequesterRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class IngestionRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: SourceRef
    status: IngestionStatus
    trigger_type: TriggerType
    requested_by: RequesterRef | None
    requested_at: datetime
    claimed_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    records_processed: int
    records_created: int
    records_updated: int
    error_count: int
    error_summary: str | None
