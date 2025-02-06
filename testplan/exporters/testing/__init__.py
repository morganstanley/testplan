# pylint: disable=undefined-all-variable
__all__ = [
    "Exporter",
    "TagFilteredExporter",
    "CoveredTestsExporter",
    "HTTPExporter",
    "JSONExporter",
    "PDFExporter",
    "TagFilteredPDFExporter",
    "WebServerExporter",
    "XMLExporter",
]
# pylint: enable=undefined-all-variable


def __getattr__(name):
    if name == "Exporter":
        from .base import Exporter

        return Exporter
    elif name == "TagFilteredExporter":
        from .tagfiltered import TagFilteredExporter

        return TagFilteredExporter
    elif name == "CoveredTestsExporter":
        from .coverage import CoveredTestsExporter

        return CoveredTestsExporter
    elif name == "HTTPExporter":
        from .http import HTTPExporter

        return HTTPExporter
    elif name == "JSONExporter":
        from .json import JSONExporter

        return JSONExporter
    elif name == "PDFExporter":
        from .pdf import PDFExporter

        return PDFExporter
    elif name == "TagFilteredPDFExporter":
        from .pdf import TagFilteredPDFExporter

        return TagFilteredPDFExporter
    elif name == "WebServerExporter":
        from .webserver import WebServerExporter

        return WebServerExporter
    elif name == "XMLExporter":
        from .xml import XMLExporter

        return XMLExporter
    else:
        import importlib

        try:
            return importlib.import_module("." + name, __name__)
        except ModuleNotFoundError:
            pass

    raise AttributeError(f"module {__name__} has no attribute {name}")
