```markdown
# API Documentation for sno_py

## Introduction

`sno_py` employs a Dependency Injection (DI) framework for managing components, leveraging containers to handle various modules such as configuration, styling, and LSP management. This document covers the usage, extension, customization of containers and styles within the `sno_py` application, along with pointers to key files in the project layout.

## Project Structure

Here's an overview of the relevant files and their locations:

- **api.md**: This documentation file.
- **__main__.py**: [Defines default containers](#containers-in-mainpy), setting up the DI framework.
- **style.py**: [Contains default styles](#default-styles-in-stylepy) used by the EditorStyle component.

## Using and Overriding Containers

### Understanding Containers

In `sno_py`, a container is an abstraction within the DI framework that manages the lifecycle and dependencies of application components. They are initialized in a centralized way and can be customized through an `.snorc` configuration file.

#### Types of Containers

- **Singleton**: Singleton containers initialize an instance once and reuse it throughout the application, making them ideal for shared state components.
- **Factory**: Factory containers create a new instance every time they are accessed, promoting state isolation and independence.

#### Lazy Loading

Containers in `sno_py` are lazy-loaded, meaning that modules are imported and instances are initialized only when first accessed. This methodology enhances performance by reducing initial load times.

### Using Containers

Containers allow you to configure and access various application components effectively:

```python
# Access a container instance
config: "Config" = container["Config"]

# Configure editor appearance
config.colorscheme = "default-dark"
config.color_depth = 24
config.show_line_numbers = True
config.expandtabs = True
config.tabstop = 4
config.show_unprintable_characters = True
config.use_system_clipboard = True
```

Containers are accessed via `container["X"]` and rely on type hints to maintain code clarity and efficacy.

### Overriding Containers

You can override containers in your personal `.snorc` file to replace default implementations with custom ones:

```python
# Replace default Config with a custom implementation
container["Config"] = "my.module.MyCustomConfig"
container["MyCustomConfig"] = Singleton
```

For this override to function, ensure that your module path is correctly included in the Python path.

### Extending Containers

To introduce new services, define them similarly to existing components and integrate them through the container:

```python
# Define a new LSP server for Python files
lsp_manager: "LanguageClientManager" = container["LanguageClientManager"]
lsp_manager.add_server(
    extensions=[".py", ".pyi"],
    command="/path/to/lsp/server",
    args=[]
)
```

### Containers in `__main__.py`

The default containers are initially defined in [__main__.py](sno_py/__main__.py), which sets up the DI patterns for components. You can customize these patterns in your configuration file without altering the main application code.

### Container Examples

Below are key examples of container usage:

- **Config**: Manages editor configuration settings.
- **EditorBuffer**: Manages buffer operations for text content.
- **LanguageClientManager**: Manages LSP servers, enriching the editor's capabilities.

## Creating Custom Color Styles with EditorStyle

### Accessing EditorStyle

Access the `EditorStyle` through the DI container to manage color schemes:

```python
# Retrieve EditorStyle instance
editor_style: "EditorStyle" = container["EditorStyle"]
```

### Adding a Custom Color Scheme

Create color schemes by defining style dictionaries and registering them with `EditorStyle`.

```python
# Define a new color scheme
custom_scheme = {
    "background": "#1E1E1E bg:#D4D4D4",
    "keyword": "#569CD6",
    "string": "#CE9178",
    "function": "#DCDCAA",
    # Other styles can be added here
}

# Register the color scheme
editor_style.add_color_scheme("custom-light", custom_scheme)
```

### Applying a Color Scheme

Apply your custom scheme by setting it in the configuration:

```python
# Set the colorscheme in Config
config: "Config" = container["Config"]
config.colorscheme = "custom-light"
```

### Example of Available Styles

Styles can be expressed in different ways. Here are examples of commonly used styles:

- **Colors**: Hex values (e.g., `#FFFFFF`)
- **Font Styles**: Keywords like `bold`, `italic`, or `underline`
- **Backgrounds**: Defined using `bg:` followed by a color (e.g., `bg:#000000`)

Combine colors and font styles seamlessly:

```python
"keyword": "#FF7B72 bold",  # Bold red
"comment": "#79740E italic",  # Italic olive
"background": "#1E1E1E bg:#FFFFFF",  # Black text on white background
```

### Available Style Tokens in `EditorStyle`

The following tokens are available when customizing your style in [`style.py`](sno_py/style.py), each needing a color or style attribute:

- **background**: Background color of the editor.
- **container**: General container styling.
- **search**: Search highlights.
- **search.current**: Current search highlight.
- **incsearch**: Incremental search highlight.
- **incsearch.current**: Current incremental highlight.
- **selected**: Styling for selected text.
- **cursor-column**: Color for the cursor's column.
- **cursor-line**: Styling for the cursor's line.
- **color-column**: Color for columns with markers.
- **matching-bracket**, **matching-bracket.other**, **matching-bracket.cursor**: Styles for matching brackets.
- **multiple-cursors**: Styling for multiple cursors.
- **line-number**, **line-number.current**: Styles for line numbering.
- **tilde**: Style for lines with tildes (no text).
- **prompt**, **prompt.arg**, **prompt.arg.text**, **prompt.search**, **prompt.search.text**: Styles for prompt configuration.
- **search-toolbar**, **system-toolbar**, **arg-toolbar**, **validation-toolbar**, **window-too-small**: Toolbar styles.
- **completion-toolbar**, **completion-menu**: Completion and menu styling.
- **scrollbar.background**, **scrollbar.button**, **scrollbar.arrow**: Scrollbar styling.
- **auto-suggestion**, **trailing-whitespace**, **tab**, **aborting**, **exiting**: Miscellaneous text and control styles.
- **digraph**, **control-character**, **nbsp**: Styles for non-printable characters.
- **terminal**, **statusbar**, **tree**, **tree_selected**: Styles for the terminal, status bar, and tree elements.
- **function**, **class**, **decorator**, **builtin**, **const**, **comment**, **string**, **number**, **operator**, **variable**, **parameter**, **type**, **type.builtin**, **escape**, **regex**, **attribute**, **markup.heading**, **markup.list**, **markup.bold**, **markup.italic**, **markup.link**, **markup.quote**, **diff.plus**, **diff.minus**, **diff.delta**, **strikethrough**, **keyword**, **lsp.error**, **lsp.warning**: Various programming syntax tokens used by tree-parser for syntax highlighter.

Each token can combine multiple styling elements, such as font attributes and colors, to enhance readability and aesthetics.

### Default Styles in `style.py`

The default styles are defined in [style.py](sno_py/style.py). This file initializes standard color and font styles used by the editor and can be extended or overridden for custom visual preferences.

## Syntax Highlighting with Tree-sitter

`sno_py` utilizes Tree-sitter for enhanced syntax highlighting, providing a modular and efficient way to highlight code. Below is a guide to set up and customize syntax highlighting:

### Installing Language Parsers

To enable syntax highlighting for specific languages, you must install the corresponding Tree-sitter language parser:

```bash
pip install tree-sitter-{language}
```

Replace `{language}` with the desired programming language you want to support (e.g., `python`, `javascript`).

### Custom Highlighting and Injection

You can customize highlighting rules using `.scm` files.

#### Highlight and Injection Files

- **MacOS:** Place custom `highlights.scm` and `injections.scm` files in `/Users/{user}/Library/Application Support/sno_py/query/{language}/`
- **Windows:** Place them in `C:\\Users\\{user}\\AppData\\Local\\sno_py\\query\\{language}\\`
- **Linux:** Place them in `/home/{user}/.local/share/sno_py/query/{language}`

These paths allow you to define custom syntax rules and language injections for each language.

The `EditorBindings` class is a foundational component in `sno_py`, responsible for managing key bindings within the editor's context. By utilizing the Dependency Injection framework, `EditorBindings` enables a flexible approach to defining and managing keyboard shortcuts. Here’s a breakdown of its components and how you can extend its functionality.

### Overview of `EditorBindings`

- **KeyBindings Management**: `EditorBindings` uses `KeyBindings` from `prompt_toolkit` to manage shortcut keys within the editor.
- **Default Bindings**: The `init_default_bindings` method initializes key bindings, attaching specific actions to various keypress sequences.
- **Conditional Execution**: Many bindings rely on conditions to ensure that actions trigger only when appropriate (e.g., the editor being in a specific mode).

### Key Features

1. **Mode Switching**: Supports navigation between modes like command mode and window command mode.
2. **Command Execution**: Allows execution of command mode inputs.
3. **Window Navigation**: Provides shortcuts to navigate between windows in an editor layout.
4. **Message Handling**: Clears messages and processes keypresses efficiently.

### Extending `EditorBindings`

To extend or customize key bindings, follow these steps:

#### 1. Adding New Key Bindings

Use the `add` method to introduce new custom key bindings:

```python
# Add a new key binding for a custom action
bindings: "EditorBindings" = container["EditorBindings"]

@bindings.add("ctrl+n", filter=~is_searching & vi_navigation_mode)
def new_buffer(_) -> None:
    """Create a new buffer when Ctrl+N is pressed."""
    editor = container["Editor"]
    editor.wm.create_new_buffer()
```

#### 2. Handling Conditional Key Binding

Conditions can be enhanced or customized to provide context-specific behavior:

```python
# Add a key binding that operates only when a certain condition is met
@bindings.add("ctrl+d", filter=Condition(lambda: editor.some_custom_condition()))
def custom_action(_) -> None:
    """Perform a custom action when Ctrl+D is pressed under specific conditions."""
    # Custom action logic here
```

#### 3. Overriding Existing Bindings

Existing bindings can be overridden by adding a new binding with the same key sequence:

```python
# Override the default behavior of the 'g' key
@bindings.add("g", filter=vi_navigation_mode)
async def custom_go_top(_) -> None:
    """Custom action when 'g' is pressed."""
    # Custom logic for top of the buffer
```

#### 4. Removing Key Bindings

While direct removal isn’t implemented, you can redefine them with no-op actions:

```python
# Disable 'Ctrl+W' by overriding it with a no-op
@bindings.add("c-w")
def noop(_) -> None:
    """No operation for this binding."""
    pass
```