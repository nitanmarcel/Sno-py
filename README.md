# Sno-py

A personal code editor I've written for myself. Because why not?

## Features

It's not so featured, it's missing a lot of things mainly because I don't use them or I was too lazy to add them.

### Implemented Features

- Vim commands like: `:w`, `:q`, `:wq`, `:qa`, `:wa`, `:wqa`, with support for `!` to force actions.
- Open files with `:e` using path autocomplete.
- Switch buffers with `:buffer` and autocomplete.
- Execute shell commands using Xonsh supporting both python and bash.
- `:set` command for configuration.
- RC files `.snorc` using python and optionally Xonsh.
- Custom color styles.
- Syntax highlighting powered by Tree-sitter.
- LSP client powered by [sansio-lsp-client](https://github.com/PurpleMyst/sansio-lsp-client).

### Commands

#### Configuration Commands

- **colorscheme**: Change active color scheme.
- **set**: Set or view configuration options. Supports options like color schemes, tab settings, etc.

#### Buffer and Window Management

- **edit (e)**: Open or switch to a file, with line position support.
- **write (w), wall (wa)**: Save current or all buffers.
- **quit (q), qall (qa)**: Quit current or all windows, with force option.
- **split (sp), vsplit, hsplit**: Split windows horizontally or vertically.
- **next (bn, wnext), previous (bp, wprevious)**: Navigate buffers or windows.
  
#### Miscellaneous

- **echo**: Display messages within the editor.
- **exec**: Run shell commands using Xonsh.

## Syntax Highlighting Customization

Sno-py uses Tree-sitter for efficient syntax highlighting. For details on setting up Tree-sitter and customizing highlighting, refer to the [API Documentation](#syntax-highlighting-with-tree-sitter).

## Usage

```
usage: [-h] [-o] [-O] [files ...]

Vim-like text editor

positional arguments:
  files              Files to open

options:
  -h, --help         show this help message and exit
  -o, --open-split   Open files in horizontal splits
  -O, --open-vsplit  Open files in vertical splits
```

## Api Documentation
Available in [api.md](api.md)

## Credits

- [prompt-toolkit](https://github.com/prompt-toolkit)
- [xonsh](https://github.com/xonsh/xonsh)
- [sansio-lsp-client](https://github.com/PurpleMyst/sansio-lsp-client)
- [py-tree-sitter](https://github.com/tree-sitter/py-tree-sitter)

## LICENSE: MIT