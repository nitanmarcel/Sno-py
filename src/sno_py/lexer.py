import importlib
from typing import Callable, Dict

from prompt_toolkit.lexers import SimpleLexer, PygmentsLexer, Lexer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text.base import StyleAndTextTuples

from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

_CACHE: Dict[str, Lexer] = {}


class FileLexer(Lexer):
    def __init__(self, editor, path: str) -> None:
        self._editor = editor
        self._path = path

    def lex_document(self, document: Document) -> Callable[[int], StyleAndTextTuples]:
        filetype = self._editor.filetype.guess_filetype(self._path, document.text)
        if filetype not in _CACHE.keys():
            known = _KNOWN_LEXERS.get(filetype, None)
            if known is not None:
                module, cls = known
                module = importlib.import_module(module)
                cls = getattr(module, cls)
                _CACHE[filetype] = PygmentsLexer(cls, sync_from_start=False)
            else:
                try:
                    _CACHE[filetype] = PygmentsLexer(
                        get_lexer_by_name(filetype).__class__
                    )
                except ClassNotFound as _:
                    _CACHE[filetype] = SimpleLexer()
        return _CACHE[filetype].lex_document(document)


_KNOWN_LEXERS = {
    "ini": ("pygments.lexers.configs", "IniLexer"),
    "cpp": ("pygments.lexers.c_cpp", "CppLexer"),
    "c": ("pygments.lexers.c_cpp", "CLexer"),
    "objc": ("pygments.lexers.objective", "ObjectiveCLexer"),
    "ocaml": ("pygments.lexers.ml", "OcamlLexer"),
    "sass": ("pygments.lexers.css", "SassLexer"),
    "zig": ("pygments.lexers.zig", "ZigLexer"),
    "gdscript": ("pygments.lexers.gdscript", "GDScriptLexer"),
    "go": ("pygments.lexers.go", "GoLexer"),
    "fsharp": ("pygments.lexers.dotnet", "FSharpLexer"),
    "meson": ("pygments.lexers.meson", "MesonLexer"),
    "ruby": ("pygments.lexers.ruby", "RubyLexer"),
    "r": ("pygments.lexers.r", "SLexer"),
    "tcl": ("pygments.lexers.tcl", "TclLexer"),
    "scss": ("pygments.lexers.css", "ScssLexer"),
    "css": ("pygments.lexers.css", "CssLexer"),
    "nim": ("pygments.lexers.nimrod", "NimrodLexer"),
    "protobuf": ("pygments.lexers.dsls", "ProtoBufLexer"),
    "java": ("pygments.lexers.jvm", "JavaLexer"),
    "erlang": ("pygments.lexers.erlang", "ErlangLexer"),
    "awk": ("pygments.lexers.textedit", "AwkLexer"),
    "coffee": ("pygments.lexers.javascript", "CoffeeScriptLexer"),
    "d": ("pygments.lexers.d", "DLexer"),
    "javascript": ("pygments.lexers.javascript", "JavascriptLexer"),
    "typescript": ("pygments.lexers.javascript", "TypeScriptLexer"),
    "gas": ("pygments.lexers.asm", "GasLexer"),
    "graphql": ("pygments.lexers.graphql", "GraphQLLexer"),
    "sh": ("pygments.lexers.shell", "BashLexer"),
    "ragel": ("pygments.lexers.parsers", "RagelLexer"),
    "html": ("pygments.lexers.html", "HtmlLexer"),
    "xml": ("pygments.lexers.html", "XmlLexer"),
    "python": ("pygments.lexers.python", "PythonLexer"),
    "html+handlebars": ("pygments.lexers.templates", "HandlebarsHtmlLexer"),
    "scala": ("pygments.lexers.jvm", "ScalaLexer"),
    "dhall": None,
    "kickstart": None,
    "swift": ("pygments.lexers.objective", "SwiftLexer"),
    "twig": ("pygments.lexers.templates", "TwigLexer"),
    "coq": ("pygments.lexers.theorem", "CoqLexer"),
    "hare": None,
    "cue": None,
    "groovy": ("pygments.lexers.jvm", "GroovyLexer"),
    "moon": ("pygments.lexers.scripting", "MoonScriptLexer"),
    "elm": ("pygments.lexers.elm", "ElmLexer"),
    "glep42": None,
    "diff": ("pygments.lexers.diff", "DiffLexer"),
    "toml": ("pygments.lexers.configs", "TOMLLexer"),
    "pascal": ("pygments.lexers.pascal", "DelphiLexer"),
    "delphi": ("pygments.lexers.pascal", "DelphiLexer"),
    "haskell": ("pygments.lexers.haskell", "HaskellLexer"),
    "julia": ("pygments.lexers.julia", "JuliaLexer"),
    "justfile": None,
    "lua": ("pygments.lexers.scripting", "LuaLexer"),
    "ledger": None,
    "gleam": None,
    "prolog": ("pygments.lexers.prolog", "PrologLexer"),
    "php": ("pygments.lexers.php", "PhpLexer"),
    "makefile": ("pygments.lexers.make", "MakefileLexer"),
    "crystal": ("pygments.lexers.crystal", "CrystalLexer"),
    "yaml": ("pygments.lexers.data", "YamlLexer"),
    "sml": ("pygments.lexers.ml", "SMLLexer"),
    "clojure": ("pygments.lexers.jvm", "ClojureLexer"),
    "taskpaper": None,
    "scheme": ("pygments.lexers.lisp", "SchemeLexer"),
    "pony": ("pygments.lexers.pony", "PonyLexer"),
    "sql": ("pygments.lexers.sql", "SqlLexer"),
    "markdown": ("pygments.lexers.markup", "MarkdownLexer"),
    "haml": ("pygments.lexers.html", "HamlLexer"),
    "asciidoc": None,
    "cucumber": ("pygments.lexers.testing", "GherkinLexer"),
    "janet": ("pygments.lexers.lisp", "JanetLexer"),
    "lisp": ("pygments.lexers.lisp", "CommonLispLexer"),
    "rust": ("pygments.lexers.rust", "RustLexer"),
    "dart": ("pygments.lexers.javascript", "DartLexer"),
    "nix": ("pygments.lexers.nix", "NixLexer"),
    "perl": ("pygments.lexers.perl", "PerlLexer"),
    "mercury": None,
    "elvish": None,
    "kotlin": ("pygments.lexers.jvm", "KotlinLexer"),
    "cmake": ("pygments.lexers.make", "CMakeLexer"),
    "odin": ("pygments.lexers.archetype", "OdinLexer"),
    "tupfile": None,
    "man": ("pygments.lexers.markup", "GroffLexer"),
    "dockerfile": ("pygments.lexers.configs", "DockerLexer"),
    "latex": ("pygments.lexers.markup", "TexLexer"),
    "typst": ("pygments.lexers.typst", "TypstLexer"),
    "fidl": None,
    "fish": ("pygments.lexers.shell", "FishShellLexer"),
    "elixir": ("pygments.lexers.erlang", "ElixirLexer"),
    "eex": None,
    "fennel": ("pygments.lexers.lisp", "FennelLexer"),
    "mlb": None,
    "ninja": None,
    "json": ("pygments.lexers.data", "JsonLexer"),
    "pug": ("pygments.lexers.html", "PugLexer"),
    "terraform": ("pygments.lexers.configs", "TerraformLexer"),
    "restructuredtext": ("pygments.lexers.markup", "RstLexer"),
    "xnosh": None,
}
