from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.selection import SelectionType
from strenum import StrEnum


class ViMode(StrEnum):
    NORMAL = "-- NORMAL --"
    INSERT = "-- INSERT --"
    REPLACE = "-- REPLACE --"
    REPLACE_SINGLE = "-- REPLACE SINGLE --"
    VISUAL = "-- VISUAL --"
    VISUAL_BLOCK = "-- VISUAL BLOCK --"
    VISUAL_LINE = "-- VISUAL LINE --"
    UNKNOWN = "-- UNKNOWN --"


def get_input_mode() -> ViMode:
    input_mode = get_app().vi_state.input_mode

    vi_mode = ViMode.NORMAL

    match input_mode:
        case InputMode.INSERT:
            vi_mode = ViMode.INSERT
        case InputMode.INSERT_MULTIPLE:
            vi_mode = ViMode.INSERT
        case InputMode.REPLACE:
            vi_mode = ViMode.REPLACE
        case InputMode.REPLACE_SINGLE:
            vi_mode = ViMode.REPLACE_SINGLE
        case InputMode.NAVIGATION:
            vi_mode = ViMode.NORMAL
        case _:
            vi_mode = ViMode.UNKNOWN
    if (state := get_app().current_buffer.selection_state) is not None:
        match state.type:
            case SelectionType.LINES:
                vi_mode = ViMode.VISUAL_LINE
            case SelectionType.BLOCK:
                vi_mode = ViMode.VISUAL_BLOCK
            case SelectionType.CHARACTERS:
                vi_mode = ViMode.VISUAL
            case _:
                return vi_mode
    return vi_mode
