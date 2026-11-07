LIKE_ESCAPE = "\\"


def like_pattern(term: str) -> str:
    """Patrón ``%término%`` con los comodines del usuario escapados (``escape=LIKE_ESCAPE``)."""
    escaped = (
        term.replace(LIKE_ESCAPE, LIKE_ESCAPE * 2)
        .replace("%", LIKE_ESCAPE + "%")
        .replace("_", LIKE_ESCAPE + "_")
    )
    return f"%{escaped}%"
