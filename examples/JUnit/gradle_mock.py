#!/usr/bin/env python

import sys
import pathlib


current_path = pathlib.Path(__file__).parent.absolute()


def output():
    sys.stdout.write(
        r"""> Configure project :

> Task :compileJava UP-TO-DATE
> Task :processResources UP-TO-DATE
> Task :classes UP-TO-DATE
> Task :compileTestJava UP-TO-DATE
> Task :processTestResources NO-SOURCE
> Task :testClasses UP-TO-DATE

> Task :test

MessageServiceTest > testGet() FAILED
    org.opentest4j.AssertionFailedError at MessageServiceTest.java:11
2021-03-19 11:11:50.150  INFO 39460 --- [extShutdownHook] o.s.s.concurrent.ThreadPoolTaskExecutor  : Shutting down ExecutorService 'applicationTaskExecutor'

> Task :test FAILED

Deprecated Gradle features were used in this build, making it incompatible with Gradle 7.0.
Use '--warning-mode all' to show the individual deprecation warnings.
See https://docs.gradle.org/6.8.2/userguide/command_line_interface.html#sec:command_line_warnings
4 actionable tasks: 1 executed, 3 up-to-date
"""
    )


def xml_output(report_dir):
    with open(
        report_dir
        / "TEST-com.gradle.example.application.ApplicationTests.xml",
        "w",
    ) as application_test:
        application_test.write(
            r"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="com.gradle.example.application.ApplicationTests" tests="1" skipped="0" failures="0" errors="0" timestamp="2021-03-19T03:11:49" hostname="example.com" time="0.228">
  <properties/>
  <testcase name="contextLoads()" classname="com.gradle.example.application.ApplicationTests" time="0.228"/>
  <system-out><![CDATA[11:11:48.002 [Test worker] DEBUG org.springframework.test.context.BootstrapUtils - Instantiating CacheAwareContextLoaderDelegate 
11:48.283 [Test worker] INFO org.springframework.boot.test.context.SpringBootTestContextBootstrapper - Using TestExecutionListeners

2021-03-19 11:11:48.665  INFO 39460 --- [    Test worker] c.m.g.e.application.ApplicationTests     : Starting ApplicationTests using Java 1.8.0_242 on localhost with PID 39460 (started by user in gradle/samples/application)
2021-03-19 11:11:48.669  INFO 39460 --- [    Test worker] c.m.g.e.application.ApplicationTests     : No active profile set, falling back to default profiles: default
2021-03-19 11:11:49.634  INFO 39460 --- [    Test worker] o.s.s.concurrent.ThreadPoolTaskExecutor  : Initializing ExecutorService 'applicationTaskExecutor'
2021-03-19 11:11:49.895  INFO 39460 --- [    Test worker] c.m.g.e.application.ApplicationTests     : Started ApplicationTests in 1.579 seconds (JVM running for 2.668)
]]></system-out>
  <system-err><![CDATA[]]></system-err>
</testsuite>"""
        )


def main():
    test_report_path = current_path / "build/test-results/test"
    test_report_path.mkdir(parents=True, exist_ok=True)
    xml_output(test_report_path)
    output()


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        main()
    else:
        raise RuntimeError("Invalid argument!")
