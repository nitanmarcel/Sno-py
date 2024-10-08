from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding import KeyBindings

from sno_py.filters import Filters


class SnoBinds(KeyBindings):
    def __init__(self, editor) -> None:
        self.editor = editor
        self.filters = Filters(editor)

        super().__init__()
        self._create_defaults()

    def _create_defaults(self):
        @self.add(
            ":", filter=self.filters.is_navigation_mode & (~self.filters.is_log_mode)
        )
        async def enter_command_mode(_) -> None:
            await self.editor.enter_command_mode()

        @self.add("escape", filter=has_focus(self.editor.command_buffer))
        async def leave_command_mode(_) -> None:
            self.editor.leave_command_mode()

        @self.add("escape", filter=self.filters.is_log_mode)
        async def leave_log_mode(_) -> None:
            self.editor.clear_log()

        @self.add("enter", filter=has_focus(self.editor.command_buffer))
        async def process_command(_) -> None:
            await self.editor.process_command()

        @self.add("enter", filter=has_focus(self.editor.log_buffer))
        async def clear_log(_) -> None:
            self.editor.clear_log()

        @self.add("tab", filter=self.filters.vi_insert_mode)
        async def add_tab(event) -> None:
            buffer = event.app.current_buffer
            if self.editor.expand_tab:
                buffer.insert_text(" " * self.editor.tabstop)
            else:
                buffer.insert_text("\t")

        @self.add("c-d", filter=~self.editor.filters.tree_menu_toggled)
        def show_tree(event):
            self.editor.layout.directory_tree.initialize()
            self.editor.show_tree_menu()

        @self.add("c-d", filter=self.editor.filters.tree_menu_toggled)
        async def close_tree(event):
            self.editor.close_tree_menu()

        @self.add("c-x", filter=~self.editor.filters.terminal_toggled)
        async def show_terminal(event):
            self.editor.layout.terminal.initialize()
            self.editor.show_terminal()

        @self.add("c-x", filter=self.editor.filters.terminal_toggled)
        async def close_terminal(event):
            self.editor.close_terminal()

        return self
