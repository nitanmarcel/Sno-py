from strenum import StrEnum

from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding.vi_state import InputMode


class ViMode(StrEnum):
    NORMAL = "-- NORMAL --"
    INSERT = "-- INSERT --"
    REPLACE = "-- REPLACE --"
    SELECT = "-- SELECT --"
    UNKNOWN = "-- UNKNOWN --"


def get_input_mode() -> ViMode:
    input_mode = get_app().vi_state.input_mode
    if input_mode in (InputMode.INSERT, InputMode.INSERT_MULTIPLE):
        return ViMode.INSERT
    if input_mode in (InputMode.REPLACE, InputMode.REPLACE_SINGLE):
        return ViMode.REPLACE
    if input_mode == InputMode.NAVIGATION:
        return ViMode.NORMAL
    if get_app().current_buffer.selection_state is not None:
        return ViMode.SELECT
    return ViMode.UNKNOWN
