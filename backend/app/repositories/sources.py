from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source


def get_by_provider_key(session: Session, provider_key: str) -> Source | None:
    return session.scalar(select(Source).where(Source.provider_key == provider_key))


def get_by_id(session: Session, source_id: int) -> Source | None:
    return session.get(Source, source_id)


def list_sources(session: Session, *, only_enabled: bool = False) -> list[Source]:
    stmt = select(Source).order_by(Source.name)
    if only_enabled:
        stmt = stmt.where(Source.is_enabled.is_(True))
    return list(session.scalars(stmt))
