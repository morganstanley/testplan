import inspect
import os


class EmphasizedDocs(type):
    EMPHASIZED_DOCS_PREFACE = inspect.cleandoc(
        """
        The most important properties that can be used in context resolution are:
        """
    )

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)

        emphasized_members = []

        for parent in bases:
            if hasattr(parent, "__emphasized__"):
                emphasized_members.extend(parent.__emphasized__)

        for name, item in dct.items():
            if item.__doc__ and "@emphasized_doc" in item.__doc__:
                if isinstance(item, property):
                    item = item.fget
                emphasized_members.append(item.__name__)

        # filter for uniques in order
        emphasized_members = list(dict.fromkeys(emphasized_members))

        emphasized_members_str = "\n\t".join(emphasized_members)
        if cls.__doc__:
            cls.__doc__ = inspect.cleandoc(cls.__doc__).format(
                emphasized_members_docs=f"{EmphasizedDocs.EMPHASIZED_DOCS_PREFACE}\n\n.. autosummary::\n\t"
                f"{emphasized_members_str}"
            )

        setattr(cls, "__emphasized__", emphasized_members)
        return cls


def emphasized(func):
    func.__doc__ = f"{func.__doc__}\n\n.. @emphasized_doc\n"
    return func


def get_metaclass_for_documentation():
    if os.getenv("DOC_MODE") is not None:
        return EmphasizedDocs
    return type
