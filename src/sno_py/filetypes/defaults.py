filetype_defaults = [
    {"ini": {"pattern": r".*(\.git(config|modules)|git/config)"}},
    {
        "cpp": {
            "file_pattern": r"\btemplate\s*<lt>|\bclass\s+\w+|\b(typename|namespace)\b|\b(public|private|protected)\s*",
            "pattern": r".*\.(cc|cpp|cxx|C|h|hh|hpp|hxx|H)$",
        }
    },
    {"c": {"pattern": r".*\.(c|h)$"}},
    {"objc": {"file_pattern": r"^[.'][A-Za-z]{2}(\s|$)", "pattern": r".*\.m"}},
    {
        "ocaml": {
            "file_pattern": r"(^\s*module)|let rec |match\s+(\S+\s)+with",
            "pattern": r".*\.(ml|mli|mll|mly)$",
        }
    },
    {"sass": {"pattern": r".*[.](sass)"}},
    {"zig": {"pattern": r".*[.](zig|zon)"}},
    {
        "gdscript": {
            "file_pattern": r"\s*(Declare|BindGlobal|KeyDependentOperation)",
            "pattern": r".*[.](gd)",
        }
    },
    {"go": {"pattern": r".*\.go"}},
    {"fsharp": {"file_pattern": r"^(: |new-device)", "pattern": r".*[.](fs|fsx|fsi)"}},
    {"cabal": {"pattern": r".*[.](cabal)"}},
    {"meson": {"pattern": r"(.*/|^)(meson\.build|meson_options\.txt)"}},
    {"eruby": {"pattern": r"'.*\.erb'"}},
    {
        "r": {
            "file_pattern": r"^(use |fn |mod |pub |macro_rules|impl|#!?$$)",
            "pattern": r"(.*/)?(\.Rprofile|.*\.[rR])",
        }
    },
    {"mail": {"pattern": r".+\.eml"}},
    {"tcl": {"pattern": r".*[.](tcl)"}},
    {"scss": {"pattern": r".*[.](scss)"}},
    {"css": {"pattern": r".*[.](css)"}},
    {"nim": {"pattern": r".*\.nim(s|ble)?"}},
    {"protobuf": {"pattern": r".*\.proto$"}},
    {"java": {"pattern": r".*\.java"}},
    {"erlang": {"pattern": r".*[.](erl|hrl)"}},
    {"awk": {"pattern": r".*\.awk"}},
    {"coffee": {"pattern": r".*[.](coffee)"}},
    {"purescript": {"pattern": r".*[.](purs)"}},
    {"gluon": {"pattern": r".*[.](glu)"}},
    {
        "d": {
            "file_pattern": r"# Microsoft Developer Studio Generated Build File",
            "pattern": r".*\.di?",
        }
    },
    {
        "javascript": {
            "file_pattern": r'"swagger":\s?"2.[0-9.]+"',
            "pattern": r".*[.][cm]?(js)x?",
        }
    },
    {
        "typescript": {
            "file_pattern": r'^\s*(import.+(from\s+|require$$)[\'"]react|\/\/\/\s*<reference\s)',
            "pattern": r".*[.][cm]?(ts)x?",
        }
    },
    {"codeowners": {"pattern": r".*/CODEOWNERS"}},
    {"gas": {"pattern": r".*\.(s|S|asm)$"}},
    {"graphql": {"pattern": r".*[.](graphqls?)"}},
    {"sh": {"pattern": r".*\.((z|ba|c|k|mk)?(sh(rc|_profile|env)?|profile))"}},
    {"ragel": {"pattern": r".*[.](ragel|rl)"}},
    {
        "html": {
            "file_pattern": r"<emu-(?:alg|annex|biblio|clause|eqn|example|figure|gann|gmod|gprose|grammar|intro|not-ref|note|nt|prodref|production|rhs|table|t|xref)(?:$|\s|>)",
            "pattern": r".*\.html",
        }
    },
    {"xml": {"pattern": r".*\.xml"}},
    {"python": {"pattern": r".*[.](py)"}},
    {"hbs": {"pattern": r".*[.](hbs)"}},
    {
        "scala": {
            "file_pattern": r"(?i:\^(this|super)\.|^\s*(~\w+\s*=\.|SynthDef\b))",
            "pattern": r".*[.](scala|sbt|sc)",
        }
    },
    {"dhall": {"pattern": r".*[.](dhall)"}},
    {"kickstart": {"pattern": r".*\.ks"}},
    {"swift": {"pattern": r".*\.(swift)"}},
    {
        "ruby": {
            "pattern": r".*(([.](rb))|(irbrc)|(pryrc)|(Brewfile)|(Capfile|[.]cap)|(Gemfile|[.]gemspec)|(Guardfile)|(Rakefile|[.]rake)|(Thorfile|[.]thor)|(Vagrantfile))"
        }
    },
    {"twig": {"pattern": r".*[.](twig)"}},
    {"coq": {"file_pattern": r"\A##fileformat=VCF", "pattern": r".*\.v"}},
    {"hare": {"pattern": r".*[.]ha"}},
    {"cue": {"pattern": r".*[.](cue)"}},
    {"groovy": {"pattern": r'"(.+\.(groovy|gvy|gy|gsh|gradle))|.+[Jj]enkinsfile.*"'}},
    {"moon": {"pattern": r".*[.](moon)"}},
    {"elm": {"pattern": r".*[.](gren)"}},
    {"glep42": {"pattern": r".*/metadata/news/.*/.*\.txt"}},
    {"diff": {"pattern": r".*\.(diff|patch)"}},
    {"toml": {"pattern": r".*\.(toml)"}},
    {"pascal": {"file_pattern": r"^\s*end[.;]", "pattern": r".*\.(p|pp|pas|pascal)$"}},
    {"delphi": {"pattern": r".*\.(dpr|dpk|dfm)$"}},
    {"freepascal": {"pattern": r".*\.(lpr|lfm)$"}},
    {"haskell": {"pattern": r".*[.](hs)"}},
    {"julia": {"pattern": r".*\.(jl)"}},
    {"justfile": {"pattern": r".*/?[jJ]ustfile"}},
    {"lua": {"pattern": r".*[.](lua|rockspec)"}},
    {"ledger": {"pattern": r".*\.ledger"}},
    {"gleam": {"pattern": r".*\.gleam"}},
    {"prolog": {"file_pattern": r"^\s*:-", "pattern": r".*[.](pl|P)"}},
    {"php": {"file_pattern": r"<\?hh", "pattern": r".*[.](phpt?)"}},
    {"makefile": {"pattern": r".*(/?[mM]akefile|\.mk|\.make)"}},
    {"crystal": {"pattern": r"'.*\.cr'"}},
    {"yaml": {"file_pattern": r"^\t+.*?[^\s:].*?:", "pattern": r".*[.](ya?ml)"}},
    {"sml": {"pattern": r".*\.(sml|fun|sig)"}},
    {"clojure": {"pattern": r".*[.](clj|cljc|cljs|cljx|edn)"}},
    {"taskpaper": {"pattern": r".*\.taskpaper"}},
    {"scheme": {"pattern": r"(.*/)?(.*\.(scm|ss|sld|sps|sls))"}},
    {"pony": {"pattern": r".*[.](pony)"}},
    {
        "sql": {
            "file_pattern": r"(?i:^\\i\b|AS\s+\$\$|LANGUAGE\s+'?plpgsql'?|BEGIN(\s+WORK)?\s*;)",
            "pattern": r".*[.]?(?i:sql)",
        }
    },
    {
        "conf": {
            "file_pattern": r"^[^#!][^:]*:",
            "pattern": r".+\.(repo|cfg|properties|desktop)",
        }
    },
    {
        "markdown": {
            "file_pattern": [r"(^[-A-Za-z0-9=#!\*$$|>])|<\/"],
            "pattern": r".*[.](markdown|md|mkd)",
        }
    },
    {"haml": {"pattern": r".*[.](haml)"}},
    {
        "asciidoc": {
            "file_pattern": r"^(----[- ]BEGIN|ssh-(rsa|dss)) ",
            "pattern": r".+\.(a(scii)?doc|asc)",
        }
    },
    {"cucumber": {"pattern": r".*[.](feature|story)"}},
    {"janet": {"pattern": r".*[.](janet|jdn)"}},
    {
        "lisp": {
            "file_pattern": r"^\s*$$(?i:defun|in-package|defpackage) ",
            "pattern": r".*[.](lisp)",
        }
    },
    {
        "rust": {
            "file_pattern": r"^(use |fn |mod |pub |macro_rules|impl|#!?$$)",
            "pattern": r".*[.](rust|rs)",
        }
    },
    {"dart": {"pattern": r".*\.dart"}},
    {"nix": {"pattern": r".*[.](nix)"}},
    {
        "perl": {
            "file_pattern": r"^\s*(?:use\s+v6\b|\bmodule\b|\bmy\s+class\b)",
            "pattern": r".*\.(t|p[lm])$",
        }
    },
    {"mercury": {"file_pattern": r"^[.'][A-Za-z]{2}(\s|$)", "pattern": r".*[.](m)"}},
    {"elvish": {"pattern": r".*\.elv"}},
    {"kotlin": {"pattern": r".*[.](kt|kts) "}},
    {"cmake": {"pattern": r".+\.cmake|.*/CMakeLists.txt"}},
    {
        "odin": {
            "file_pattern": r"(?:^|<)\s*[A-Za-z0-9_]+\s*=\s*<",
            "pattern": r".*\.odin",
        }
    },
    {"tupfile": {"pattern": r".*/?Tup(file|rules)(\.\w+)?$"}},
    {
        "troff": {
            "file_pattern": r'^\.(?:[A-Za-z]{2}(?:\s|$)|\\")',
            "pattern": r".*\.\d+",
        }
    },
    {"dockerfile": {"pattern": r".*/?Dockerfile(\..+)?$"}},
    {"latex": {"pattern": r".*\.(tex|cls|sty|dtx)"}},
    {"typst": {"file_pattern": r"^#(import|show|let|set)", "pattern": r".*[.](typ)"}},
    {"fidl": {"pattern": r".*\.fidl"}},
    {"fish": {"pattern": r".*[.](fish)"}},
    {
        "elixir": {
            "file_pattern": [
                r"^\s*@moduledoc\s",
                r"^\s*(?:cond|import|quote|unless)\s",
                r"^\s*def(?:exception|impl|macro|module|protocol)[(\s]",
            ],
            "pattern": r".*[.](ex|exs)",
        }
    },
    {"eex": {"pattern": r".*[.]html[.][lh]?eex"}},
    {"fennel": {"pattern": r".*[.]fnl"}},
    {"mlb": {"pattern": r".*\.mlb"}},
    {"ninja": {"pattern": r".+\.ninja"}},
    {"json": {"file_pattern": r'"swagger":\s?"2.[0-9.]+"', "pattern": r".*[.](json)"}},
    {"pug": {"pattern": r".*[.](pug|jade)"}},
    {"terraform": {"pattern": r".*[.](tf|tfvars)"}},
    {"restructuredtext": {"pattern": r".*[.](rst)"}},
    {"xnosh": {"pattern": r".*(xsh|xonshrc|snorc)$"}},
]
