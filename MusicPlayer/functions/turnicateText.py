def truncate(text: str, width: int) -> str:
    if len(text) > width:
        return text[:width - 1] + "…"
    return text