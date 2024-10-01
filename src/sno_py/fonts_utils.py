from sno_py.icons import icons


def get_language_icon(language_id: str) -> str:
    return icons.get(f"seti-{language_id}", icons.get("seti-text"))


def get_icon(tag: str) -> str:
    return icons.get(tag, "")
