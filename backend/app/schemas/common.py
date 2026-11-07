from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, ConfigDict

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class Page[T](BaseModel):
    """Página de un listado (ADD §11.3)."""

    items: list[T]
    total: int
    page: int
    page_size: int


class Pagination(BaseModel):
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination(
    page: Annotated[int, Query(ge=1, le=100_000, description="Página, desde 1")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description="Filas por página")
    ] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(page=page, page_size=page_size)


class SourceRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_key: str
    name: str
