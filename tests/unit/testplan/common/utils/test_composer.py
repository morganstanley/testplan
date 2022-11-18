import sys

import pytest

from testplan.common.utils.composer import compose_contexts


def _context_manager_gen(
    name: str, will_raise: bool = False, will_catch: bool = False
):
    class _Inner:
        def __enter__(self):
            sys.stdout.write(f"entering {name}\n")
            if will_raise:
                sys.stdout.write(f"raised by {name}\n")
                return 1 / 0
            return f"r{name}"

        def __exit__(self, exc_type, exc_value, traceback):
            # we want to distinguish exceptions thrown by __enter__
            # from exceptions thrown by the "with" body
            if exc_type is not None and exc_type is not ZeroDivisionError:
                if will_catch:
                    sys.stdout.write(f"caught by {name}\n")
                    sys.stdout.write(f"leaving {name}\n")
                    return True
            sys.stdout.write(f"leaving {name}\n")

    return _Inner


def test_compose_contexts_single(capsys):
    """
    The elementary case.
    """

    with compose_contexts(_context_manager_gen("a")()) as ra:
        assert ra == "ra"

    expected = ["entering a", "leaving a"]
    captured = capsys.readouterr().out.strip().split("\n")
    assert captured == expected


def test_compose_contexts_all_pass(capsys):
    """
    The everyone's happy case.
    """

    a = _context_manager_gen("a")
    b = _context_manager_gen("b")
    c = _context_manager_gen("c")
    with compose_contexts(a(), b(), c()) as (ra, rb, rc):
        assert ra == "ra"
        assert rb == "rb"
        assert rc == "rc"

    expected = [f"entering {n}" for n in ("a", "b", "c")] + [
        f"leaving {n}" for n in ("c", "b", "a")
    ]
    captured = capsys.readouterr().out.strip().split("\n")
    assert captured == expected


def test_compose_contexts_all_fail(capsys):
    """
    If some outer context manager fails at __enter__,
    our composer should immediately raise without going any further.
    """

    with pytest.raises(ZeroDivisionError):
        a = _context_manager_gen("a", will_raise=True)
        b = _context_manager_gen("b", will_raise=True)
        c = _context_manager_gen("c", will_raise=True)
        with compose_contexts(a(), b(), c()):
            pass

    expected = ["entering a", "raised by a"]
    captured = capsys.readouterr().out.strip().split("\n")
    assert captured == expected


def test_compose_contexts_inner_fail(capsys):
    """
    If some inner context manager fails at __enter__,
    our composer should bubble the error to the outside world.
    """

    with pytest.raises(ZeroDivisionError):
        a = _context_manager_gen("a", will_catch=True)
        b = _context_manager_gen("b")
        c = _context_manager_gen("c", will_raise=True)
        d = _context_manager_gen("d")
        with compose_contexts(a(), b(), c(), d()) as rs:
            assert rs == NotImplemented
            raise NotImplementedError("this will never be executed")

    expected = (
        [f"entering {n}" for n in ("a", "b", "c")]
        + ["raised by c"]
        + [f"leaving {n}" for n in ("b", "a")]
    )
    captured = capsys.readouterr().out.strip().split("\n")
    assert captured == expected


def test_compose_contexts_body_fail_caught(capsys):
    """
    If all the __enter__ have passed and something fails inside our
    composed context, we should allow those individual context managers
    to handle it.
    """

    a = _context_manager_gen("a", will_catch=True)
    b = _context_manager_gen("b", will_catch=True)
    c = _context_manager_gen("c")
    d = _context_manager_gen("d")
    with compose_contexts(a(), b(), c(), d()) as rs:
        assert rs == ("ra", "rb", "rc", "rd")
        sys.stdout.write("raised by body\n")
        raise RuntimeError("haha")

    expected = (
        [f"entering {n}" for n in ("a", "b", "c", "d")]
        + ["raised by body", "leaving d", "leaving c", "caught by b"]
        + ["leaving b", "leaving a"]
    )
    captured = capsys.readouterr().out.strip().split("\n")
    assert captured == expected


def test_compose_contexts_body_fail_raised(capsys):
    """
    if those individual context managers cannot handle the exception,
    it will be bubbled out for sure.
    """

    with pytest.raises(RuntimeError):
        a = _context_manager_gen("a")
        b = _context_manager_gen("b")
        c = _context_manager_gen("c")
        d = _context_manager_gen("d")
        with compose_contexts(a(), b(), c(), d()) as rs:
            assert rs == ("ra", "rb", "rc", "rd")
            sys.stdout.write("raised by body\n")
            raise RuntimeError("haha")

    expected = (
        [f"entering {n}" for n in ("a", "b", "c", "d")]
        + ["raised by body"]
        + [f"leaving {n}" for n in ("d", "c", "b", "a")]
    )
    captured = capsys.readouterr().out.strip().split("\n")
    assert captured == expected
