from typing import Any, Union
from attr import define, field, validators
from prompt_toolkit.output.color_depth import ColorDepth
import appdirs


def positive_int(_: Any, attribute: Any, value: int) -> None:
    """Validate that a given integer attribute is positive.

    Args:
        _ (Any): Placeholder for the instance of the class.
        attribute (Any): The attribute being validated.
        value (int): The value to validate.

    Raises:
        ValueError: If the value is not a positive integer.
    """
    if value <= 0:
        raise ValueError(f"{attribute.name} must be a positive integer")


def color_depth_converter(value: Union[int, ColorDepth]) -> ColorDepth:
    """Convert an integer or ColorDepth to a valid ColorDepth enum.

    Args:
        value (int | ColorDepth): The value to convert.

    Returns:
        ColorDepth: The corresponding ColorDepth enum.
    """
    if isinstance(value, ColorDepth):
        return value
    if value <= 0:
        return ColorDepth.DEPTH_1_BIT
    elif value <= 4:
        return ColorDepth.DEPTH_4_BIT
    elif value <= 8:
        return ColorDepth.DEPTH_8_BIT
    else:
        return ColorDepth.DEPTH_24_BIT


@define
class Config:
    """Configuration settings for the application.

    Attributes:
        colorscheme (str): The color scheme used by the application.
        color_depth (ColorDepth): The color depth setting.
        use_nerd_icons (bool): Flag to use nerd icons.
        show_line_numbers (bool): Flag to show line numbers in the editor.
        show_relative_numbers (bool): Flag to show relative line numbers.
        expandtabs (bool): Flag to use spaces instead of tabs.
        tabstop (int): The number of spaces per tab character.
        show_unprintable_characters (bool): Flag to display unprintable characters.
        use_system_clipboard (bool): Flag to use the system clipboard integration.
        user_data_dir (str): Directory for user data.
        user_cache_dir (str): Directory for user cache.
        user_config_dir (str): Directory for user configuration.
        user_log_dir (str): Directory for user logs.
    """

    colorscheme: str = field(default="default", validator=validators.instance_of(str))
    color_depth: ColorDepth = field(
        default=ColorDepth.DEFAULT,
        validator=validators.instance_of(ColorDepth | int),
        converter=color_depth_converter,
    )
    use_nerd_icons: bool = field(default=False, validator=validators.instance_of(bool))
    show_line_numbers: bool = field(
        default=True, validator=validators.instance_of(bool)
    )
    show_relative_numbers: bool = field(
        default=True, validator=validators.instance_of(bool)
    )
    expandtabs: bool = field(default=True, validator=validators.instance_of(bool))
    tabstop: int = field(
        default=4, validator=[validators.instance_of(int), positive_int]
    )
    show_unprintable_characters: bool = field(
        default=True, validator=validators.instance_of(bool)
    )
    use_system_clipboard: bool = field(
        default=True, validator=validators.instance_of(bool)
    )

    user_data_dir: str = field(default=appdirs.user_data_dir(appname="sno.py"))
    user_cache_dir: str = field(default=appdirs.user_cache_dir(appname="sno.py"))
    user_config_dir: str = field(default=appdirs.user_config_dir(appname="sno.py"))
    user_log_dir: str = field(default=appdirs.user_log_dir(appname="sno.py"))

    @property
    def queries_dir(self) -> str:
        """Get the directory path for queries.

        Returns:
            str: The full path to the queries directory.
        """
        import os

        return os.path.join(self.user_data_dir, "query")
