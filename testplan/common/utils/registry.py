"""Provides Registry mapping utility."""
from testplan.common.utils import logger


class Registry(logger.Loggable):
    """
    A utility that provides a decorator (`@registry.bind`) for
    mapping objects to another (decorated) class.

    Supports absolute or category based
    defaults via `@registry.bind_default` decorator as well.

    Example:

    >>> registry = Registry()

    >>> class ClassA:
        ... pass

    >>>  # instances of ClassA are now bound to ClassB for this registry
    >>> @registry.bind(ClassA)
    >>> class ClassB:
        ... pass


    >>> obj_a = ClassA()

    >>> registry[obj_a] is ClassB
    ... True
    """

    def __init__(self):
        self.data = {}
        self._default = None
        self._category_defaults = {}
        super(Registry, self).__init__()

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        if self._default is not None:
            raise ValueError(
                "Cannot re-bind default value. (Existing: {})".format(
                    self.default
                )
            )
        self._default = value

    def get_lookup_key(self, obj):
        """
        This method is used for generating the key when do a lookup
        from the registry. Object class is used by default.
        """
        return obj.__class__

    def get_record_key(self, obj):
        """
        This method is used for generating the key when we bind
        an object (possibly a class) via the registry.
        """
        return obj

    def get_category(self, obj):
        """
        Override this to define logic for generating
        the category key from the object instance.
        """
        try:
            return getattr(obj, "category", obj["category"])
        except KeyError:
            # User has registered defaults for a category
            # however category retrieval from object failed
            # Need to fail explicitly and warn the user
            if self._category_defaults:
                raise NotImplementedError(
                    "Could not retrieve category information from: {}."
                    "You may need to override `get_category`"
                    "of the registry.".format(obj)
                )
            raise

    def _get_default(self, obj):
        try:
            return self._category_defaults[self.get_category(obj)]
        except KeyError:
            if self._default:
                return self._default
        raise KeyError("No mapping found for: {}".format(obj))

    def __getitem__(self, item):
        try:
            return self.data[self.get_lookup_key(item)]
        except KeyError:
            return self._get_default(item)

    def __setitem__(self, key, value):
        key = self.get_record_key(key)
        self.data[key] = value

    def bind(self, *classes):
        """
        Decorator for binding one or more classes to another.

        :param classes: One or more classes that
                        will be bound to the decorated class.
        """

        def wrapper(value):
            for kls in classes:
                self[kls] = value
            return value

        return wrapper

    def bind_default(self, category=None):
        """
        Decorator for binding a class as category based or absolute default.

        :param category: (optional) If provided, the decorated class will
                         be the default for the given category, otherwise
                         it will be the absolute default.
        """

        def wrapper(value):
            if category:
                if category in self._category_defaults:
                    raise ValueError(
                        "Cannot overwrite default value "
                        "for category: {}".format(category)
                    )
                self._category_defaults[category] = value
            else:
                self.default = value
            return value

        return wrapper
