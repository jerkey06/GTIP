from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import IngestionStatus


class LastRunSummary(BaseModel):
    id: int
    status: IngestionStatus
    requested_at: datetime
    finished_at: datetime | None
    records_processed: int
    records_created: int
    records_updated: int
    error_count: int


class SourceRead(BaseModel):
    id: int
    provider_key: str
    name: str
    description: str | None
    base_url: str | None
    # Habilitada en la base de datos y con conector y configuración disponibles.
    is_enabled: bool
    disabled_reason: str | None
    requires_api_key: bool
    # None si la fuente no usa clave. Nunca se devuelve el valor de la clave.
    api_key_configured: bool | None
    schedule_interval_minutes: int | None
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    last_run: LastRunSummary | None
    active_run_id: int | None
