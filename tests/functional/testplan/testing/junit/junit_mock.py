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

    sys.stderr.write(
        r"""
2 tests completed, 1 failed

FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':test'.
> There were failing tests. See the report at: file:///samples/application/build/reports/tests/test/index.html

* Try:
Run with --stacktrace option to get the stack trace. Run with --info or --debug option to get more log output. Run with --scan to get full insights.

* Get more help at https://help.gradle.org

BUILD FAILED in 4s
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

    with open(
        report_dir
        / "TEST-com.gradle.example.application.MessageServiceTest.xml",
        "w",
    ) as message_test:
        message_test.write(
            r"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="com.gradle.example.application.MessageServiceTest" tests="1" skipped="0" failures="1" errors="0" timestamp="2021-03-19T03:11:47" hostname="localhost" time="0.021">
  <properties/>
  <testcase name="testGet()" classname="com.gradle.example.application.MessageServiceTest" time="0.021">
    <failure message="org.opentest4j.AssertionFailedError: expected: &lt;Hello JUnit 5&gt; but was: &lt;abcde&gt;" type="org.opentest4j.AssertionFailedError">org.opentest4j.AssertionFailedError: expected: &lt;Hello JUnit 5&gt; but was: &lt;abcde&gt;
        at org.junit.jupiter.api.AssertionUtils.fail(AssertionUtils.java:55)
        at org.junit.jupiter.api.AssertionUtils.failNotEqual(AssertionUtils.java:62)
        at org.junit.jupiter.api.AssertEquals.assertEquals(AssertEquals.java:182)
        at org.junit.jupiter.api.AssertEquals.assertEquals(AssertEquals.java:177)
        at org.junit.jupiter.api.Assertions.assertEquals(Assertions.java:1124)
        at com.gradle.example.application.MessageServiceTest.testGet(MessageServiceTest.java:11)
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
        at java.lang.reflect.Method.invoke(Method.java:498)
        at org.junit.platform.commons.util.ReflectionUtils.invokeMethod(ReflectionUtils.java:688)
        at org.junit.jupiter.engine.execution.MethodInvocation.proceed(MethodInvocation.java:60)
        at org.junit.jupiter.engine.execution.InvocationInterceptorChain$ValidatingInvocation.proceed(InvocationInterceptorChain.java:131)
        at org.junit.jupiter.engine.extension.TimeoutExtension.intercept(TimeoutExtension.java:149)
        at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestableMethod(TimeoutExtension.java:140)
        at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestMethod(TimeoutExtension.java:84)
        at org.junit.jupiter.engine.execution.ExecutableInvoker$ReflectiveInterceptorCall.lambda$ofVoidMethod$0(ExecutableInvoker.java:115)
        at org.junit.jupiter.engine.execution.ExecutableInvoker.lambda$invoke$0(ExecutableInvoker.java:105)
        at org.junit.jupiter.engine.execution.InvocationInterceptorChain$InterceptedInvocation.proceed(InvocationInterceptorChain.java:106)
        at org.junit.jupiter.engine.execution.InvocationInterceptorChain.proceed(InvocationInterceptorChain.java:64)
        at org.junit.jupiter.engine.execution.InvocationInterceptorChain.chainAndInvoke(InvocationInterceptorChain.java:45)
        at org.junit.jupiter.engine.execution.InvocationInterceptorChain.invoke(InvocationInterceptorChain.java:37)
        at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:104)
        at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:98)
        at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.lambda$invokeTestMethod$6(TestMethodTestDescriptor.java:210)
        at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
        at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.invokeTestMethod(TestMethodTestDescriptor.java:206)
        at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:131)
        at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:65)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$5(NodeTestTask.java:139)
        at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$7(NodeTestTask.java:129)
        at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:127)
        at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:126)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:84)
        at java.util.ArrayList.forEach(ArrayList.java:1257)
        at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:38)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$5(NodeTestTask.java:143)
        at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$7(NodeTestTask.java:129)
        at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:127)
        at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:126)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:84)
        at java.util.ArrayList.forEach(ArrayList.java:1257)
        at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:38)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$5(NodeTestTask.java:143)
        at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$7(NodeTestTask.java:129)
        at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:127)
        at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:126)
        at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:84)
        at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.submit(SameThreadHierarchicalTestExecutorService.java:32)
        at org.junit.platform.engine.support.hierarchical.HierarchicalTestExecutor.execute(HierarchicalTestExecutor.java:57)
        at org.junit.platform.engine.support.hierarchical.HierarchicalTestEngine.execute(HierarchicalTestEngine.java:51)
        at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:108)
        at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:88)
        at org.junit.platform.launcher.core.EngineExecutionOrchestrator.lambda$execute$0(EngineExecutionOrchestrator.java:54)
        at org.junit.platform.launcher.core.EngineExecutionOrchestrator.withInterceptedStreams(EngineExecutionOrchestrator.java:67)
        at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:52)
        at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:96)
        at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:75)
        at org.gradle.api.internal.tasks.testing.junitplatform.JUnitPlatformTestClassProcessor$CollectAllTestClassesExecutor.processAllTestClasses(JUnitPlatformTestClassProcessor.java:99)
        at org.gradle.api.internal.tasks.testing.junitplatform.JUnitPlatformTestClassProcessor$CollectAllTestClassesExecutor.access$000(JUnitPlatformTestClassProcessor.java:79)
        at org.gradle.api.internal.tasks.testing.junitplatform.JUnitPlatformTestClassProcessor.stop(JUnitPlatformTestClassProcessor.java:75)
        at org.gradle.api.internal.tasks.testing.SuiteTestClassProcessor.stop(SuiteTestClassProcessor.java:61)
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
        at java.lang.reflect.Method.invoke(Method.java:498)
        at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:36)
        at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
        at org.gradle.internal.dispatch.ContextClassLoaderDispatch.dispatch(ContextClassLoaderDispatch.java:33)
        at org.gradle.internal.dispatch.ProxyDispatchAdapter$DispatchingInvocationHandler.invoke(ProxyDispatchAdapter.java:94)
        at com.sun.proxy.$Proxy2.stop(Unknown Source)
        at org.gradle.api.internal.tasks.testing.worker.TestWorker.stop(TestWorker.java:133)
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
        at java.lang.reflect.Method.invoke(Method.java:498)
        at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:36)
        at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
        at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:182)
        at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:164)
        at org.gradle.internal.remote.internal.hub.MessageHub$Handler.run(MessageHub.java:414)
        at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:64)
        at org.gradle.internal.concurrent.ManagedExecutorImpl$1.run(ManagedExecutorImpl.java:48)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
        at org.gradle.internal.concurrent.ThreadFactoryImpl$ManagedThreadRunnable.run(ThreadFactoryImpl.java:56)
        at java.lang.Thread.run(Thread.java:748)
</failure>
  </testcase>
  <system-out><![CDATA[]]></system-out>
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
