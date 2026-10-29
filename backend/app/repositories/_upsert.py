from dataclasses import dataclass


@dataclass
class UpsertResult:
    """Cuántas filas de un lote se crearon, cambiaron o ya estaban iguales."""

    created: int = 0
    updated: int = 0
    unchanged: int = 0

    @property
    def processed(self) -> int:
        return self.created + self.updated + self.unchanged

    def __iadd__(self, other: "UpsertResult") -> "UpsertResult":
        self.created += other.created
        self.updated += other.updated
        self.unchanged += other.unchanged
        return self


def chunks[T](items: list[T], size: int) -> list[list[T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]
