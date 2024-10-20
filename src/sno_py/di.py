import importlib
from typing import Any, Dict, Type, TypeVar, Union

T = TypeVar("T")


class LazyLoader:
    """A utility class for lazy loading of modules and classes.

    Attributes:
        module_name (str): The name of the module to load.
        class_name (str): The name of the class to load from the module.
        _class (Any | None): The loaded class, if it has already been loaded.
    """

    def __init__(self, module_name: str, class_name: str):
        """Initialize the LazyLoader with a module and class name.

        Args:
            module_name (str): The name of the module to load.
            class_name (str): The name of the class to load from the module.
        """
        self.module_name = module_name
        self.class_name = class_name
        self._class = None

    def load(self) -> Any:
        """Load the class specified by the module and class name.

        Returns:
            Any: The loaded class.
        """
        if self._class is None:
            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
        return self._class


class Factory:
    """Marker class indicating that an object is a factory."""

    pass


class Singleton:
    """Marker class indicating that an object is a singleton."""

    pass


class Container:
    """A dependency injection container for managing object lifecycles.

    Attributes:
        _registry (Dict[Union[Type[T], str], Any]): A registry of keys to object instances, factories, or singletons.
        _instances (Dict[Union[Type[T], str], Any]): A cache of singleton instances.
    """

    def __init__(self):
        """Initialize the container with empty registries."""
        self._registry: Dict[Union[Type[T], str], Any] = {}
        self._instances: Dict[Union[Type[T], str], Any] = {}

    def __setitem__(self, key: Union[Type[T], str], value: Any) -> None:
        """Register a value with the container.

        Args:
            key (Type[T] | str): The key for storing the value.
            value (Any): The value to store, which can be a class, instance, Factory, Singleton, or lazy-loaded string.

        Raises:
            KeyError: If the key is not already registered when setting a Factory or Singleton.
            ValueError: If the value type is invalid for registration.
        """
        if isinstance(value, str) and "." in value:
            module_name, class_name = value.rsplit(".", 1)
            self._registry[key] = LazyLoader(module_name, class_name)
        elif value in (Factory, Singleton):
            if key not in self._registry:
                raise KeyError(f"Key '{key}' not registered in container")
            self._registry[key] = (self._registry[key], value)
        elif isinstance(key, type) and isinstance(value, key):
            self._registry[key] = lambda: value
        elif isinstance(key, str):
            self._registry[key] = value
        else:
            raise ValueError(
                "Invalid value type. Expected Factory, Singleton, instance, or class for string keys."
            )

    def __getitem__(self, key: Union[Type[T], str]) -> Any:
        """Retrieve a value from the container by its key.

        Args:
            key (Type[T] | str): The key of the value to retrieve.

        Returns:
            Any: The registered object, creating it if necessary.

        Raises:
            KeyError: If the key is not found in the registry.
        """
        if key not in self._registry:
            raise KeyError(f"Key '{key}' not registered in container")

        value = self._registry[key]

        if isinstance(value, tuple):
            lazy_loader, pattern = value
            cls = lazy_loader.load()
            if pattern == Singleton:
                if key not in self._instances:
                    self._instances[key] = cls()
                return self._instances[key]
            elif pattern == Factory:
                return cls
        elif isinstance(value, LazyLoader):
            return value.load()()
        elif callable(value):
            return value()
        else:
            return value


container = Container()
