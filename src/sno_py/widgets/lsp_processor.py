from typing import TYPE_CHECKING, Union
from prompt_toolkit.layout.processors import (
    Processor,
    Transformation,
    TransformationInput,
)
from prompt_toolkit.layout.utils import explode_text_fragments
from sansio_lsp_client import Range
from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.window import WindowManager
    from sno_py.buffer import EditorBuffer


class LspReportsProcessor(Processor):
    """A processor for handling LSP reports, highlighting errors and warnings in the text.

    Attributes:
        wm (WindowManager | None): Reference to the window manager.
    """

    def __init__(self) -> None:
        """Initialize the LSP Reports Processor."""
        super().__init__()
        self.wm: Union["WindowManager", None] = None

    def apply_transformation(
        self, transformation_input: TransformationInput
    ) -> Transformation:
        """Apply transformations to highlight LSP reports on the text fragments.

        Args:
            transformation_input (TransformationInput): Input containing the text fragments and line number.

        Returns:
            Transformation: Transformed text with error and warning styling applied.
        """
        if self.wm is None:
            self.wm = container["WindowManager"]

        fragments = transformation_input.fragments
        active_buffer: Union["EditorBuffer", None] = self.wm.active_window.active_buffer

        if active_buffer is not None:
            for report in active_buffer.lsp_reports:
                rrange: Range = report["range"]
                is_error: bool = report["is_error"]
                if rrange.start.line == transformation_input.lineno:
                    fragments = explode_text_fragments(fragments)
                    for i in range(rrange.start.character, rrange.end.character):
                        style_cls = (
                            "class:lsp.error" if is_error else "class:lsp.warning"
                        )
                        if i < len(fragments):
                            fragments[i] = (style_cls, fragments[i][1])

        return Transformation(fragments)
