"""Example test script for use by PyTest."""
# For the most basic usage, no imports are required.
# pytest will automatically detect any test cases based
# on methods starting with ``test_``.


class TestClassOne(object):
    # Trivial test method that will simply cause the test to succeed.
    # Note the use of the plain Python assert statement.
    def test_success(self):
        assert True

    # Similar to above, except this time the test case will always fail.
    def test_failure(self):
        assert False
