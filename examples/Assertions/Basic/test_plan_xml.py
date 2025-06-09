#!/usr/bin/env python
# This plan contains tests that demonstrate failures as well.
"""
This example shows usage of xml assertion namespaces.
"""

import re
import sys
from testplan import test_plan
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.report.testing.styles import Style, StyleEnum


@testsuite
class XMLSuite:
    """
    `result.xml` namespace can be used for applying advanced assertion
    logic onto XML data.
    """

    @testcase
    def test_xml_namespace(self, env, result):
        # `xml.check` can be used for checking if given tags & XML namespaces
        # contain the expected values

        xml_1 = """
                <Root>
                    <Test>Foo</Test>
                </Root>
            """

        result.xml.check(
            element=xml_1,
            xpath="/Root/Test",
            description="Simple XML check for existence of xpath.",
        )

        xml_2 = """
                <Root>
                    <Test>Value1</Test>
                    <Test>Value2</Test>
                </Root>
            """

        result.xml.check(
            element=xml_2,
            xpath="/Root/Test",
            tags=["Value1", "Value2"],
            description="XML check for tags in the given xpath.",
        )

        xml_3 = """
                <SOAP-ENV:Envelope
                  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
                    <SOAP-ENV:Header/>
                    <SOAP-ENV:Body>
                        <ns0:message
                          xmlns:ns0="http://testplan">Hello world!</ns0:message>
                    </SOAP-ENV:Body>
                </SOAP-ENV:Envelope>
            """

        result.xml.check(
            element=xml_3,
            xpath="//*/a:message",
            tags=[re.compile(r"Hello*")],
            namespaces={"a": "http://testplan"},
            description="XML check with namespace matching.",
        )


@test_plan(
    name="XML Assertions Example",
    stdout_style=Style(
        passing=StyleEnum.ASSERTION_DETAIL, failing=StyleEnum.ASSERTION_DETAIL
    ),
)
def main(plan):
    plan.add(
        MultiTest(
            name="XML Assertions Test",
            suites=[
                XMLSuite(),
            ],
        )
    )


if __name__ == "__main__":
    sys.exit(not main())
