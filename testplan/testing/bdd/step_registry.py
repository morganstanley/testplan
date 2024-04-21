import os
import threading
from collections import deque
from importlib.util import module_from_spec, spec_from_file_location
from typing import Deque

from testplan.testing.bdd.parsers import RegExParser, Parser


class _StepImporterPathContext:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        StepRegistry.get_load_steps_path_stack().append(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        StepRegistry.get_load_steps_path_stack().pop()


def import_step_base(path):
    return _StepImporterPathContext(path)


class StepRegistry:
    local = threading.local()
    count = 0

    def __init__(self):
        self.func_map = {}
        self.default_parser = RegExParser
        self._actual_parser = None
        self.prefix = "sputnik_step_registry_import_prefix_{}".format(
            self.count
        )
        self.__class__.count += 1

    @property
    def actual_parser(self):
        return self._actual_parser

    @actual_parser.setter
    def actual_parser(self, parser_class):
        if issubclass(parser_class, Parser):
            self._actual_parser = parser_class
        else:
            raise TypeError("actual_parser need to be a subcalss of Parser")

    def register(self, sentence_or_parser, func):
        if isinstance(sentence_or_parser, str):

            parser_class = self.default_parser
            if self._actual_parser:
                parser_class = self._actual_parser
            parser = parser_class(sentence_or_parser)

        elif isinstance(sentence_or_parser, Parser):
            parser = sentence_or_parser

        self.func_map[parser] = func

    def get(self, sentence):
        for parser, func in self.func_map.items():
            match = parser.match(sentence)
            if match:
                return parser.bind(func, match)
        return None

    def load_steps(self, definition_file, step_parser_class):
        self.local.target_registry = self
        path, filename = os.path.split(definition_file)
        basename, ext = os.path.splitext(filename)

        # replace '.' to '_' as the file called feature.steps so python do not think it is a module
        # also prefix it with the unique prefix of this registry, so different registries will load to
        # different modules
        modulename = "{}_{}".format(self.prefix, basename.replace(".", "_"))
        self.actual_parser = step_parser_class
        with import_step_base(path):
            spec = spec_from_file_location(modulename, definition_file)
            if spec:
                module = module_from_spec(spec)
                spec.loader.exec_module(module)

    @classmethod
    def get_target_registry(cls) -> "StepRegistry":
        return cls.local.target_registry

    @classmethod
    def get_load_steps_path_stack(cls) -> Deque[str]:
        cls.local.path_stack = (
            cls.local.path_stack
            if hasattr(cls.local, "path_stack")
            else deque()
        )
        return cls.local.path_stack

    @classmethod
    def import_step_base(cls) -> str:
        return cls.get_load_steps_path_stack()[-1]


def import_steps(relative_path):
    registry = StepRegistry.get_target_registry()
    assert registry
    parser = registry.actual_parser
    registry.load_steps(
        os.path.join(registry.import_step_base(), relative_path), parser
    )
    registry.actual_parser = parser


def set_actual_parser(parser):
    StepRegistry.get_target_registry().actual_parser = parser


def step(sentence_or_parser):
    """
    Step Decorator

    :param sentence: The regexp it matches
    :return:
    """

    def factory(func):
        StepRegistry.get_target_registry().register(sentence_or_parser, func)
        return func

    return factory


Given = step
When = step
Then = step
And = step
But = step


# This is for backward compatibility for step definitions used to use
# the singleton 'THE_STEP_REGISTRY' now it proxy to the right registry


class __StepRegistryCompatProxy:
    def __getattr__(self, item):
        return getattr(StepRegistry.get_target_registry(), item)


THE_STEP_REGISTRY = __StepRegistryCompatProxy()
