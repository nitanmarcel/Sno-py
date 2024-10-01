from prompt_toolkit.application import get_app
from prompt_toolkit.filters import (Condition, vi_insert_mode,
                                    vi_navigation_mode)


class Filters:
    def __init__(self, editor) -> None:
        self._editor = editor
        
        self._is_tree_menu_toggled = False
        self._is_terminal_toggled = False

        class _Conditions:
            @Condition
            def vi_buffer_focused() -> bool:
                app = get_app()
                if (
                    app.layout.has_focus(self._editor.search_buffer)
                    or app.layout.has_focus(self._editor.command_buffer)
                    or app.layout.has_focus(self._editor.log_buffer)
                ):
                    return True
                return False

            @Condition
            def vi_log_focused():
                app = get_app()
                return _Conditions.vi_buffer_focused() and app.layout.has_focus(
                    self._editor.log_buffer
                )

            @Condition
            def vi_command_focused():
                app = get_app()
                return _Conditions.vi_buffer_focused() and app.layout.has_focus(
                    self._editor.command_buffer
                )
            
            @Condition
            def tree_menu_toggled():
                return self._is_tree_menu_toggled
            
            @Condition
            def terminal_toggled():
                return self._is_terminal_toggled

        self.vi_buffer_focused = _Conditions.vi_buffer_focused
        self.is_command_mode = _Conditions.vi_command_focused
        self.is_log_mode = _Conditions.vi_log_focused

        self.is_navigation_mode = vi_navigation_mode
        self.vi_insert_mode = vi_insert_mode  
        
        self.tree_menu_toggled = _Conditions.tree_menu_toggled
        self.terminal_toggled = _Conditions.terminal_toggled
        
    
    def tree_menu_toggle(self):
        self._is_tree_menu_toggled = not self._is_tree_menu_toggled
        return self._is_tree_menu_toggled
    
    def terminal_toggle(self):
        self._is_terminal_toggled = not self._is_terminal_toggled
        return self._is_terminal_toggled