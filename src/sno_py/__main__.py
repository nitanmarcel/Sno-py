import argparse
from typing import TYPE_CHECKING
from anyio import run, Path
from sno_py.di import Factory, Singleton, container

if TYPE_CHECKING:
    from sno_py.xsh import Xsh
    from sno_py.editor import Editor


def register_components():
    """Register components and their instantiation patterns in the container."""
    container["Xsh"] = "sno_py.xsh.Xsh"
    container["Xsh"] = Singleton

    container["TreeSitterLexer"] = "sno_py.lexer.TreeSitterLexer"
    container["TreeSitterLexer"] = Factory

    container["Config"] = "sno_py.config.Config"
    container["Config"] = Singleton

    container["FileType"] = "sno_py.filetypes.filetypes.FileType"
    container["FileType"] = Singleton

    container["WindowManager"] = "sno_py.window.WindowManager"
    container["WindowManager"] = Singleton

    container["SplitContainer"] = "sno_py.window.SplitContainer"
    container["SplitContainer"] = Factory

    container["EditorWindow"] = "sno_py.window.EditorWindow"
    container["EditorWindow"] = Factory

    container["EditorBuffer"] = "sno_py.buffer.EditorBuffer"
    container["EditorBuffer"] = Factory

    container["Editor"] = "sno_py.editor.Editor"
    container["Editor"] = Singleton

    container["ProcessorsStorage"] = "sno_py.storage.processors.ProcessorsStorage"
    container["ProcessorsStorage"] = Singleton

    container["BarsStorage"] = "sno_py.storage.bars.BarsStorage"
    container["BarsStorage"] = Singleton

    container["StatusBar"] = "sno_py.widgets.statusbar.StatusBar"
    container["StatusBar"] = Factory

    container["CommandBar"] = "sno_py.widgets.commandbar.CommandBar"
    container["CommandBar"] = Factory

    container["TabBar"] = "sno_py.widgets.tabbar.TabBar"
    container["TabBar"] = Factory

    container["MessageBar"] = "sno_py.widgets.messagebar.MessageBar"
    container["MessageBar"] = Factory

    container["SearchBar"] = "sno_py.widgets.searchbar.SearchBar"
    container["SearchBar"] = Factory

    container["LspReporterBar"] = "sno_py.widgets.lspreportbar.LspReporterBar"
    container["LspReporterBar"] = Factory

    container["LspCompleter"] = "sno_py.widgets.lsp_completions.LspCompleter"
    container["LspCompleter"] = Singleton

    container["LspReportsProcessor"] = (
        "sno_py.widgets.lsp_processor.LspReportsProcessor"
    )
    container["LspReportsProcessor"] = Factory

    container["EditorStyle"] = "sno_py.style.EditorStyle"
    container["EditorStyle"] = Singleton

    container["EditorBindings"] = "sno_py.bindings.EditorBindings"
    container["EditorBindings"] = Singleton

    container["CommandHandler"] = "sno_py.commands.handler.CommandHandler"
    container["CommandHandler"] = Singleton

    container["CompleteHandler"] = "sno_py.commands.completer.CompleteHandler"
    container["CompleteHandler"] = Singleton

    container["LanguageClientManager"] = "sno_py.lsp.manager.LanguageClientManager"
    container["LanguageClientManager"] = Singleton


async def entry():
    """Entry point for the asynchronous execution of the editor."""
    parser = argparse.ArgumentParser(description="Vim-like text editor")
    parser.add_argument("files", nargs="*", help="Files to open")
    parser.add_argument(
        "-o",
        "--open-split",
        action="store_true",
        help="Open files in horizontal splits",
    )
    parser.add_argument(
        "-O", "--open-vsplit", action="store_true", help="Open files in vertical splits"
    )

    args = parser.parse_args()

    editor: "Editor" = container["Editor"]

    home = await Path.home()
    snorc_py = home / ".snorc"
    snorc_xsh = home / ".snorc.xsh"

    if await snorc_py.is_file():
        content = await snorc_py.read_text()
        exec(content, {"container": container})
    elif await snorc_xsh.is_file():
        xsh: "Xsh" = container["Xsh"]
        content = await snorc_xsh.read_text()
        await xsh.load_snorc(content)

    await editor.run(args)


def main():
    """Main entry point for the application."""
    register_components()
    try:
        import uvloop

        run(entry, backend_options={"loop_factory": uvloop.new_event_loop})
    except (ImportError, ModuleNotFoundError):
        run(entry)


if __name__ == "__main__":
    main()
