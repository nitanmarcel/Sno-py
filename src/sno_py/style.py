from typing import TYPE_CHECKING

from prompt_toolkit.styles import Style

from sno_py.di import container

if TYPE_CHECKING:
    from sno_py.config import Config


class EditorStyle:
    """Manage and apply color schemes for the editor interface.

    Attributes:
        config (Config): Configuration settings for the editor.
        colorschemes (dict): A dictionary of available color schemes.
        _cache (dict): A cache for storing generated styles.
    """

    def __init__(self) -> None:
        """Initialize the EditorStyle with default settings and styles."""
        self.config: "Config" = container["Config"]
        self.colorschemes = {}
        self.init_default()
        self._cache: dict = {}

    def add_color_scheme(self, name: str, style: dict) -> None:
        """Add a new color scheme to the styles.

        Args:
            name (str): The name of the color scheme.
            style (dict): A dictionary containing style definitions.
        """
        self.colorschemes[name] = style

    def get_colorschemes(self) -> list[str]:
        """Get a list of available color scheme names.

        Returns:
            list[str]: A list of color scheme names.
        """
        return list(self.colorschemes.keys())

    def get_style(self) -> Style:
        """Retrieve and return the active style based on the current configuration.

        Returns:
            Style: The prompt_toolkit Style object for the active color scheme.
        """
        default_style = self.colorschemes["default"]

        if self.config.colorscheme in self._cache:
            return self._cache[self.config.colorscheme]

        self._cache.clear()

        if self.config.colorscheme:
            user_style = self.colorschemes.get(self.config.colorscheme, {})
            self._cache[self.config.colorscheme] = Style.from_dict(
                {**default_style, **user_style}
            )
        else:
            self._cache[self.config.colorscheme] = Style.from_dict(default_style)

        return self._cache[self.config.colorscheme]

    def init_default(self) -> None:
        """Initialize and add the default color schemes."""
        default_style = {
            "background": "#2E3440 bg:#ECEFF4",
            "container": "#2E3440 bg:#ECEFF4",
            "search": "#ECEFF4",
            "search.current": "#ECEFF4",
            "incsearch": "#ECEFF4",
            "incsearch.current": "#2E3440",
            "selected": "#2E3440",
            "cursor-column": "#4C566A",
            "cursor-line": "underline",
            "color-column": "#81A1C1",
            "matching-bracket": "#81A1C1",
            "matching-bracket.other": "#2E3440",
            "matching-bracket.cursor": "#A3BE8C",
            "multiple-cursors": "#2E3440",
            "line-number": "#4C566A",
            "line-number.current": "bold",
            "tilde": "#81A1C1",
            "prompt": "",
            "prompt.arg": "noinherit",
            "prompt.arg.text": "",
            "prompt.search": "noinherit",
            "prompt.search.text": "",
            "search-toolbar": "bold",
            "search-toolbar.text": "nobold",
            "system-toolbar": "bold",
            "system-toolbar.text": "nobold",
            "arg-toolbar": "bold",
            "arg-toolbar.text": "nobold",
            "validation-toolbar": "#ECEFF4",
            "window-too-small": "#ECEFF4",
            "completion-toolbar": "#4C566A",
            "completion-toolbar.arrow": "#4C566A bold",
            "completion-toolbar.completion": "#4C566A",
            "completion-toolbar.completion.current": "#5E81AC",
            "completion-menu.completion": "",
            "completion-menu.completion.current": "#4C566A",
            "completion-menu.meta.completion": "#81A1C1",
            "completion-menu.meta.completion.current": "#81A1C1",
            "completion-menu.multi-column-meta": "#81A1C1",
            "scrollbar.background": "#4C566A",
            "scrollbar.button": "#5E81AC",
            "scrollbar.arrow": "noinherit bold",
            "auto-suggestion": "#4C566A",
            "trailing-whitespace": "#4C566A",
            "tab": "#4C566A",
            "aborting": "#4C566A",
            "exiting": "#4C566A",
            "digraph": "#81A1C1",
            "control-character": "#5E81AC",
            "nbsp": "underline #A3BE8C",
            "terminal": "#2E3440 bg:#ECEFF4",
            "statusbar": "#ECEFF4 bg:#4C566A",
            "tree": "#2E3440 bg:#E5E9F0",
            "tree_selected": "#ECEFF4 bg:#5E81AC",
            "function": "#8FBCBB",
            "class": "#88C0D0 bold",
            "decorator": "#D08770 italic",
            "builtin": "#81A1C1",
            "const": "#B48EAD",
            "comment": "#4C566A italic",
            "string": "#A3BE8C",
            "number": "#D08770",
            "operator": "#81A1C1 bold",
            "variable": "#2E3440",
            "parameter": "#4C566A italic",
            "type": "#81A1C1",
            "type.builtin": "#81A1C1 bold",
            "escape": "#EBCB8B bold",
            "regex": "#EBCB8B",
            "attribute": "#D08770",
            "markup.heading": "#5E81AC bold",
            "markup.list": "#81A1C1",
            "markup.bold": "#2E3440 bold",
            "markup.italic": "#2E3440 italic",
            "markup.link": "#5E81AC underline",
            "markup.quote": "#4C566A italic",
            "diff.plus": "#A3BE8C",
            "diff.minus": "#BF616A",
            "diff.delta": "#EBCB8B",
            "strikethrough": "strike",
            "keyword": "#5E81AC",
            "lsp.error": "#BF616A bold",
            "lsp.warning": "#EBCB8B bold",
        }

        self.add_color_scheme("default", default_style)

        default_dark_style = {
            "background": "#D8DEE9 bg:#2E3440",
            "container": "#D8DEE9 bg:#2E3440",
            "search": "#2E3440",
            "search.current": "#2E3440",
            "incsearch": "#2E3440",
            "incsearch.current": "#D8DEE9",
            "selected": "#D8DEE9",
            "cursor-column": "#616E88",
            "cursor-line": "underline",
            "color-column": "#8FBCBB",
            "matching-bracket": "#8FBCBB",
            "matching-bracket.other": "#D8DEE9",
            "matching-bracket.cursor": "#A3BE8C",
            "multiple-cursors": "#D8DEE9",
            "line-number": "#616E88",
            "line-number.current": "bold",
            "tilde": "#8FBCBB",
            "prompt": "",
            "prompt.arg": "noinherit",
            "prompt.arg.text": "",
            "prompt.search": "noinherit",
            "prompt.search.text": "",
            "search-toolbar": "bold",
            "search-toolbar.text": "nobold",
            "system-toolbar": "bold",
            "system-toolbar.text": "nobold",
            "arg-toolbar": "bold",
            "arg-toolbar.text": "nobold",
            "validation-toolbar": "#2E3440",
            "window-too-small": "#2E3440",
            "completion-toolbar": "#616E88",
            "completion-toolbar.arrow": "#616E88 bold",
            "completion-toolbar.completion": "#616E88",
            "completion-toolbar.completion.current": "#88C0D0",
            "completion-menu.completion": "",
            "completion-menu.completion.current": "#616E88",
            "completion-menu.meta.completion": "#8FBCBB",
            "completion-menu.meta.completion.current": "#8FBCBB",
            "completion-menu.multi-column-meta": "#8FBCBB",
            "scrollbar.background": "#616E88",
            "scrollbar.button": "#88C0D0",
            "scrollbar.arrow": "noinherit bold",
            "auto-suggestion": "#616E88",
            "trailing-whitespace": "#616E88",
            "tab": "#616E88",
            "aborting": "#616E88",
            "exiting": "#616E88",
            "digraph": "#8FBCBB",
            "control-character": "#88C0D0",
            "nbsp": "underline #A3BE8C",
            "terminal": "#D8DEE9 bg:#2E3440",
            "statusbar": "#2E3440 bg:#4C566A",
            "tree": "#D8DEE9 bg:#3B4252",
            "tree_selected": "#2E3440 bg:#88C0D0",
            "keyword": "#88C0D0 bold",
            "function": "#8FBCBB",
            "class": "#81A1C1 bold",
            "decorator": "#D08770 italic",
            "builtin": "#81A1C1",
            "const": "#B48EAD",
            "comment": "#616E88 italic",
            "string": "#A3BE8C",
            "number": "#D08770",
            "operator": "#81A1C1 bold",
            "variable": "#D8DEE9",
            "parameter": "#E5E9F0 italic",
            "type": "#8FBCBB",
            "type.builtin": "#8FBCBB bold",
            "escape": "#EBCB8B bold",
            "regex": "#EBCB8B",
            "attribute": "#D08770",
            "markup.heading": "#88C0D0 bold",
            "markup.list": "#81A1C1",
            "markup.bold": "#D8DEE9 bold",
            "markup.italic": "#D8DEE9 italic",
            "markup.link": "#88C0D0 underline",
            "markup.quote": "#616E88 italic",
            "diff.plus": "#A3BE8C",
            "diff.minus": "#BF616A",
            "diff.delta": "#EBCB8B",
            "strikethrough": "strike",
            "lsp.error": "#BF616A bold",
            "lsp.warning": "#EBCB8B bold",
        }

        self.add_color_scheme("default-dark", default_dark_style)
