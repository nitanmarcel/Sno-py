
_STRINGS = {
    "not_saved": "No write since last change",
    "read_only": "Buffer is read only",
    "unknown_error": "Unknown error"
}


def get_string(id: str) -> str:
    if id in _STRINGS.keys():
        return _STRINGS[id]
    return _STRINGS["unknown_error"]
