from testplan.common.utils.registry import Registry


def test_registry():
    reg = Registry()

    class MyClass:
        pass

    @reg.bind(MyClass)
    class OtherClass:
        pass

    assert reg.data[MyClass] is OtherClass, "bind operation failed"
    assert reg[MyClass()] is OtherClass, "obj lookup failed"
