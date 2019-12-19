from testplan.report import TestReport, TestGroupReport, TestCaseReport

expected_report = TestReport(
    name="plan",
    entries=[
        TestGroupReport(
            name="MyHobbesTest",
            category="hobbestest",
            entries=[
                TestGroupReport(
                    name="Hog",
                    category="suite",
                    entries=[
                        TestCaseReport(
                            name="MultiDestination",
                            entries=[{
                                u'category': u'DEFAULT',
                                u'description': u'MultiDestination',
                                u'line_no': None,
                                u'content': u'5.01973s',
                                u'meta_type': u'assertion',
                                u'passed': True,
                                u'type': 'RawAssertion'}]),
                        TestCaseReport(
                            name="KillAndResume",
                            entries=[{
                                u'category': u'DEFAULT',
                                u'description': u'KillAndResume',
                                u'line_no': None,
                                u'content': u'27.5463s',
                                u'meta_type': u'assertion',
                                u'passed': True,
                                u'type': 'RawAssertion'}]),
                        TestCaseReport(
                            name="RestartEngine",
                            entries=[{
                                u'category': u'DEFAULT',
                                u'description': u'RestartEngine',
                                u'line_no': None,
                                u'content': u'18.4997s',
                                u'meta_type': u'assertion',
                                u'passed': True, u'type': 'RawAssertion'}]),
                        TestCaseReport(
                            name="Cleanup",
                            entries=[{
                                u'category': u'DEFAULT',
                                u'description': u'Cleanup',
                                u'line_no': None,
                                u'content': u'140.089ms',
                                u'meta_type': u'assertion',
                                u'passed': True,
                                u'type': 'RawAssertion'}])],
                    tags=None),
                TestGroupReport(
                    name="Net",
                    category="suite",
                    entries=[
                        TestCaseReport(
                            name="syncClientAPI",
                            entries=[{
                                u'category': u'DEFAULT',
                                u'description': u'syncClientAPI',
                                u'line_no': None,
                                u'content': u'4.66587s',
                                u'meta_type': u'assertion',
                                u'passed': True,
                                u'type': 'RawAssertion'}]),
                        TestCaseReport(
                            name="asyncClientAPI",
                            entries=[{
                                u'category': u'DEFAULT',
                                u'description': u'asyncClientAPI',
                                u'line_no': None,
                                u'content': u'1.4305s',
                                u'meta_type': u'assertion',
                                u'passed': True,
                                u'type': 'RawAssertion'}])],
                    tags=None),
                TestGroupReport(
                    name="Recursives",
                    category="suite",
                    entries=[
                        TestCaseReport(
                            name="Lists",
                            entries=[{
                                u'category': u'DEFAULT',
                                u'description': u'Lists',
                                u'line_no': None,
                                u'content': u'2.98303s',
                                u'meta_type': u'assertion',
                                u'passed': True,
                                u'type': 'RawAssertion'}])],
                    tags=None)],
            tags=None)])

expected_output =\
'''MyHobbesTest
  Arrays
  Compiler
  Definitions
  Existentials
  Hog
  Matching
  Net
  Objects
  Prelude
  Recursives
  Storage
  Structs
  TypeInf
  Variants
'''