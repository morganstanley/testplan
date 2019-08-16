"""Interactive mode tests."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import range
from builtins import next
from future import standard_library
standard_library.install_aliases()
import os
import re

import pytest
import six
import requests
import pytest

from testplan.common.utils.timing import wait
from testplan.common.utils.comparison import compare
from testplan.common.utils.context import context
from testplan.common.utils.timing import get_sleeper
from testplan.common.entity.base import Environment

from testplan import Testplan
from testplan.common.utils.logger import TEST_INFO, DEBUG
from testplan.testing.multitest import MultiTest, testsuite, testcase
from testplan.environment import LocalEnvironment
from testplan.testing.multitest.driver.tcp import TCPServer, TCPClient

from testplan.common.utils.testing import log_propagation_disabled
from testplan.common.utils.logger import TESTPLAN_LOGGER


THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def _assert_http_response(response, operation, mode,
                          result=None, error=False, metadata=None, trace=None):
    assert response == {
        'result': result, 'error': error,
        'metadata': metadata or {}, 'trace': trace,
        'message': '{} operation performed: {}'.format(mode, operation)}


class InteractivePlan(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __enter__(self):
        self._plan = Testplan(**self._kwargs)
        return self._plan

    def __exit__(self, *args):
        self._plan.abort()


@testsuite
class BasicSuite(object):

    @testcase(parameters=range(3))
    def basic_case(self, env, result, arg):
        result.equal(1, 1, description='Passing assertion')


@testsuite
class TCPSuite(object):
    def __init__(self, arg):
        self.arg = arg

    def suite_name(self):
        return 'Custom_{}'.format(self.arg)

    @testcase
    def send_and_receive_msg(self, env, result):
        """
        Client sends a message, server received and responds back.
        """
        bytes_sent = env.client.send_text('hello')
        received = env.server.receive_text(size=bytes_sent)
        result.equal(received, 'hello', 'Server received')

        bytes_sent = env.server.send_text('world')
        received = env.client.receive_text(size=bytes_sent)
        result.equal(received, 'world', 'Client received')


def make_multitest(idx=''):
    def accept_connection(env):
        # Server accepts client connection.
        env.server.accept_connection()

    return MultiTest(
        name='Test{}'.format(idx),
        suites=[BasicSuite(), TCPSuite(0), TCPSuite(1)],
        environment=[
            TCPServer(name='server'),
            TCPClient(name='client',
                      host=context('server', '{{host}}'),
                      port=context('server', '{{port}}'))],
        after_start=accept_connection)


def test_top_level_tests():
    with log_propagation_disabled(TESTPLAN_LOGGER):
        with InteractivePlan(
              name='InteractivePlan',
              interactive=True, interactive_block=False,
              parse_cmdline=False, logger_level=TEST_INFO) as plan:
            plan.add(make_multitest(1))
            plan.run()
            wait(lambda: bool(plan.i.http_handler_info),
                 5, raise_on_timeout=True)
            plan.add(make_multitest(2))  # Added after plan.run()
            assert isinstance(plan.i.test('Test1'), MultiTest)
            assert isinstance(plan.i.test('Test2'), MultiTest)

            # print_report(plan.i.report(serialized=True))

            # TESTS AND ASSIGNED RUNNERS
            assert list(plan.i.all_tests()) ==\
                   [('Test1', 'local_runner'), ('Test2', 'local_runner')]

            # OPERATE TEST DRIVERS (start/stop)
            resources = [res.uid() for res in plan.i.test('Test2').resources]
            assert resources == ['server', 'client']
            for resource in plan.i.test('Test2').resources:
                assert resource.status.tag is None
            plan.i.start_test_resources('Test2')  # START
            for resource in plan.i.test('Test2').resources:
                assert resource.status.tag is resource.STATUS.STARTED
            plan.i.stop_test_resources('Test2')  # STOP
            for resource in plan.i.test('Test2').resources:
                assert resource.status.tag is resource.STATUS.STOPPED

            # RESET REPORTS
            plan.i.reset_reports()
            from .reports.basic_top_level_reset import REPORT as BTLReset
            assert compare(BTLReset, plan.i.report(serialized=True))[0] is True

            # RUN ALL TESTS
            plan.i.run_tests()
            from .reports.basic_top_level import REPORT as BTLevel
            assert compare(BTLevel, plan.i.report(serialized=True))[0] is True

            # RESET REPORTS
            plan.i.reset_reports()
            from .reports.basic_top_level_reset import REPORT as BTLReset
            assert compare(BTLReset, plan.i.report(serialized=True))[0] is True

            # RUN SINGLE TESTSUITE (CUSTOM NAME)
            plan.i.run_test_suite('Test2', 'TCPSuite - Custom_1')
            from .reports.basic_run_suite_test2 import REPORT as BRSTest2
            assert compare(BRSTest2, plan.i.test_report('Test2'))[0] is True

            # RUN SINGLE TESTCASE
            plan.i.run_test_case('Test1', '*', 'basic_case__arg_1')
            from .reports.basic_run_case_test1 import REPORT as BRCTest1
            assert compare(BRCTest1, plan.i.test_report('Test1'))[0] is True


def test_top_level_environment():
    with log_propagation_disabled(TESTPLAN_LOGGER):
        with InteractivePlan(
              name='InteractivePlan',
              interactive=True, interactive_block=False,
              parse_cmdline=False, logger_level=TEST_INFO) as plan:
            plan.add_environment(
                LocalEnvironment(
                    'env1',
                    [TCPServer(name='server'),
                     TCPClient(name='client',
                               host=context('server', '{{host}}'),
                               port=context('server', '{{port}}'))]))
            plan.run()
            wait(lambda: bool(plan.i.http_handler_info),
                 5, raise_on_timeout=True)

            assert len(plan.resources.environments.envs) == 1

            # Create an environment using serializable arguments.
            # That is mandatory for HTTP usage.
            plan.i.create_new_environment('env2')
            plan.i.add_environment_resource('env2', 'TCPServer',
                                            name='server')
            plan.i.add_environment_resource('env2', 'TCPClient',
                                            name='client',
                                            _ctx_host_ctx_driver='server',
                                            _ctx_host_ctx_value='{{host}}',
                                            _ctx_port_ctx_driver='server',
                                            _ctx_port_ctx_value='{{port}}')
            plan.i.add_created_environment('env2')

            assert len(plan.resources.environments.envs) == 2

            for env_uid in ('env1', 'env2'):
                env = plan.i.get_environment(env_uid)
                assert isinstance(env, Environment)
                resources = [res.uid() for res in env]
                assert resources == ['server', 'client']
                for resource in env:
                    assert resource.status.tag is None
                plan.i.start_environment(env_uid) # START

                # INSPECT THE CONTEXT WHEN STARTED
                env_context = plan.i.get_environment_context(env_uid)
                for resource in [res.uid() for res in env]:
                    res_context = \
                        plan.i.environment_resource_context(env_uid, resource_uid=resource)
                    assert env_context[resource] == res_context
                    assert isinstance(res_context['host'], six.string_types)
                    assert isinstance(res_context['port'], int)
                    assert res_context['port'] > 0

                # CUSTOM RESOURCE OPERATIONS
                plan.i.environment_resource_operation(
                    env_uid, 'server', 'accept_connection')
                plan.i.environment_resource_operation(
                    env_uid, 'client', 'send_text', msg='hello')
                received = plan.i.environment_resource_operation(
                    env_uid, 'server', 'receive_text')
                assert received == 'hello'
                plan.i.environment_resource_operation(
                    env_uid, 'server', 'send_text', msg='worlds')
                received = plan.i.environment_resource_operation(
                    env_uid, 'client', 'receive_text')
                assert received == 'worlds'

                for resource in env:
                    assert resource.status.tag is resource.STATUS.STARTED
                plan.i.stop_environment(env_uid)  # STOP
                for resource in env:
                    assert resource.status.tag is resource.STATUS.STOPPED

def post_request(url, data):
    headers = {'content-type': 'text/json'}
    return requests.post(url, headers=headers, json=data)


def test_http_operate_tests_sync():
    with log_propagation_disabled(TESTPLAN_LOGGER):
        with InteractivePlan(
              name='InteractivePlan',
              interactive=True, interactive_block=False,
              parse_cmdline=False, logger_level=TEST_INFO) as plan:
            plan.run()
            wait(lambda: any(plan.i.http_handler_info),
                 5, raise_on_timeout=True)
            addr = 'http://{}:{}'.format(*plan.i.http_handler_info)

            plan.add(make_multitest(1))
            plan.add(make_multitest(2))

            # OPERATE TEST DRIVERS (start/stop)
            for resource in plan.i.test('Test2').resources:
                assert resource.status.tag is None
            response = post_request(
                '{}/sync/start_test_resources'.format(addr),
                {'test_uid': 'Test2'}).json()
            _assert_http_response(response, 'start_test_resources', 'Sync')

            for resource in plan.i.test('Test2').resources:
                assert resource.status.tag is resource.STATUS.STARTED
            response = post_request(
                '{}/sync/stop_test_resources'.format(addr),
                {'test_uid': 'Test2'}).json()
            _assert_http_response(response, 'stop_test_resources', 'Sync')
            for resource in plan.i.test('Test2').resources:
                assert resource.status.tag is resource.STATUS.STOPPED

            # RESET REPORTS
            response = post_request(
                '{}/sync/reset_reports'.format(addr), {}).json()
            _assert_http_response(response, 'reset_reports', 'Sync')
            from .reports.basic_top_level_reset import REPORT as BTLReset
            result = compare(BTLReset, plan.i.report(serialized=True))
            assert result[0] is True

            # RUN ALL TESTS
            response = post_request(
                '{}/sync/run_tests'.format(addr), {}).json()
            _assert_http_response(response, 'run_tests', 'Sync')
            from .reports.basic_top_level import REPORT as BTLevel
            result = compare(BTLevel, plan.i.report(serialized=True))
            assert result[0] is True

            # RESET REPORTS
            response = post_request(
                '{}/sync/reset_reports'.format(addr), {}).json()
            _assert_http_response(response, 'reset_reports', 'Sync')

            from .reports.basic_top_level_reset import REPORT as BTLReset
            assert compare(BTLReset, plan.i.report(serialized=True))[0] is True

            # REPORT VIA HTTP
            response = post_request(
                '{}/sync/report'.format(addr),
                {'serialized': True}).json()
            expected_response = {
                'result': plan.i.report(serialized=True),
                'error': False, 'metadata': {}, 'trace': None,
                'message': 'Sync operation performed: report'}
            assert compare(response, expected_response)[0] is True

            # RUN SINGLE TESTSUITE (CUSTOM NAME)
            response = post_request(
                '{}/sync/run_test_suite'.format(addr),
                {'test_uid': 'Test2',
                 'suite_uid': 'TCPSuite - Custom_1'}).json()
            _assert_http_response(response, 'run_test_suite', 'Sync')
            from .reports.basic_run_suite_test2 import REPORT as BRSTest2
            assert compare(BRSTest2, plan.i.test_report('Test2'))[0] is True

            # TEST 2 REPORT VIA HTTP
            response = post_request(
                '{}/sync/test_report'.format(addr),
                {'test_uid': 'Test2'}).json()
            expected_response = {
                'result': plan.i.test_report('Test2'),
                'error': False, 'metadata': {}, 'trace': None,
                'message': 'Sync operation performed: test_report'}
            assert compare(response, expected_response)[0]is True

            # RUN SINGLE TESTCASE
            response = post_request(
                '{}/sync/run_test_case'.format(addr),
                {'test_uid': 'Test1',
                 'suite_uid': '*',
                 'case_uid': 'basic_case__arg_1'}).json()
            _assert_http_response(response, 'run_test_case', 'Sync')
            from .reports.basic_run_case_test1 import REPORT as BRCTest1
            assert compare(BRCTest1, plan.i.test_report('Test1'))[0] is True

            # TEST 1 REPORT VIA HTTP
            response = post_request(
                '{}/sync/test_report'.format(addr),
                {'test_uid': 'Test1'}).json()
            expected_response = {
                'result': plan.i.test_report('Test1'),
                'error': False, 'metadata': {}, 'trace': None,
                'message': 'Sync operation performed: test_report'}
            assert compare(response, expected_response)[0] is True


def test_http_operate_tests_async():
    with log_propagation_disabled(TESTPLAN_LOGGER):
        with InteractivePlan(
              name='InteractivePlan',
              interactive=True, interactive_block=False,
              parse_cmdline=False, logger_level=TEST_INFO) as plan:
            plan.run()
            wait(lambda: any(plan.i.http_handler_info),
                 5, raise_on_timeout=True)
            addr = 'http://{}:{}'.format(*plan.i.http_handler_info)

            plan.add(make_multitest(1))
            plan.add(make_multitest(2))

            # TRIGGER ASYNC RUN OF TESTS -> UID
            response = post_request(
                '{}/async/run_tests'.format(addr), {}).json()
            expected = {
                'message': 'Async operation performed: run_tests',
                'error': False, 'trace': None, 'metadata': {},
                'result': re.compile('[0-9|a-z|-]+')}
            assert compare(expected, response)[0] is True
            uid = response['result']

            # QUERY UID ASYNC OPERATION UNTIL FINISHED
            sleeper = get_sleeper(
                0.6, raise_timeout_with_msg='Async result missing.')
            while next(sleeper):
                response = post_request(
                    '{}/async_result'.format(addr),
                    {'uid': uid})
                json_response = response.json()
                if json_response['error'] is False:
                    assert response.status_code == 200
                    expected = {
                        'result': None, 'trace': None, 'error': False,
                        'message': re.compile('[0-9|a-z|-]+'),
                        'metadata': {'state': 'Finished'}}
                    assert compare(expected, json_response)[0] is True
                    break
                assert response.status_code == 400

            # REPORT VIA HTTP
            response = post_request(
                '{}/sync/report'.format(addr),
                {'serialized': True}).json()
            expected_response = {
                'result': plan.i.report(serialized=True),
                'error': False, 'metadata': {}, 'trace': None,
                'message': 'Sync operation performed: report'}
            assert compare(response, expected_response)[0] is True


def test_http_dynamic_environments():

    def add_second_client_after_environment_started():
        # ADD A DRIVER IN EXISTING RUNNING ENVIRONMENT
        response = post_request(
            '{}/sync/add_environment_resource'.format(addr),
            {'env_uid': 'env1',
             'target_class_name': 'TCPClient',
             'name': 'client2',
             '_ctx_host_ctx_driver': 'server',
             '_ctx_host_ctx_value': '{{host}}',
             '_ctx_port_ctx_driver': 'server',
             '_ctx_port_ctx_value': '{{port}}'}).json()
        _assert_http_response(response, 'add_environment_resource', 'Sync')

        # START THE DRIVER
        response = post_request(
            '{}/sync/environment_resource_start'.format(addr),
            {'env_uid': 'env1',
             'resource_uid': 'client2'}).json()
        _assert_http_response(response, 'environment_resource_start', 'Sync')

        # SERVER ACCEPT CONNECTION
        response = post_request(
            '{}/sync/environment_resource_operation'.format(addr),
            {'env_uid': 'env1',
             'resource_uid': 'server',
             'res_op': 'accept_connection'}).json()
        _assert_http_response(
            response, 'environment_resource_operation', 'Sync',
            result=1)

        # CLIENT SENDS MESSAGE
        msg = 'Hello world'
        response = post_request(
            '{}/sync/environment_resource_operation'.format(addr),
            {'env_uid': 'env1',
             'resource_uid': 'client2',
             'res_op': 'send_text',
             'msg': msg}).json()
        _assert_http_response(
            response, 'environment_resource_operation', 'Sync',
            result=len(msg))

        # SERVER RECEIVES
        response = post_request(
            '{}/sync/environment_resource_operation'.format(addr),
            {'env_uid': 'env1',
             'resource_uid': 'server',
             'res_op': 'receive_text'}).json()
        _assert_http_response(
            response, 'environment_resource_operation', 'Sync',
            result=msg)

    with InteractivePlan(
          name='InteractivePlan',
          interactive=True, interactive_block=False,
          parse_cmdline=False, logger_level=DEBUG) as plan:
        plan.run()
        wait(lambda: any(plan.i.http_handler_info),
             5, raise_on_timeout=True)
        addr = 'http://{}:{}'.format(*plan.i.http_handler_info)

        # CREATE NEW ENVIRONMENT CREATOR
        response = post_request(
            '{}/sync/create_new_environment'.format(addr),
            {'env_uid': 'env1'}).json()
        _assert_http_response(response, 'create_new_environment', 'Sync')

        # ADD A TCP SERVER TO ENVIRONMENT
        response = post_request(
            '{}/sync/add_environment_resource'.format(addr),
            {'env_uid': 'env1',
             'target_class_name': 'TCPServer',
             'name': 'server'}).json()
        _assert_http_response(response, 'add_environment_resource', 'Sync')

        # ADD A TCP CLIENT TO ENVIRONMENT USING CONTEXT
        response = post_request(
            '{}/sync/add_environment_resource'.format(addr),
            {'env_uid': 'env1',
             'target_class_name': 'TCPClient',
             'name': 'client',
             '_ctx_host_ctx_driver': 'server',
             '_ctx_host_ctx_value': '{{host}}',
             '_ctx_port_ctx_driver': 'server',
             '_ctx_port_ctx_value': '{{port}}'}).json()
        _assert_http_response(response, 'add_environment_resource', 'Sync')

        # ADD THE ENVIRONMENT TO PLAN
        response = post_request(
            '{}/sync/add_created_environment'.format(addr),
            {'env_uid': 'env1'}).json()
        _assert_http_response(response, 'add_created_environment', 'Sync')
        print(878)

        # START THE ENVIRONMENT
        response = post_request(
            '{}/sync/start_environment'.format(addr),
            {'env_uid': 'env1'}).json()
        _assert_http_response(
            response, 'start_environment', 'Sync',
            result={'client': 'STARTED', 'server': 'STARTED'})

        # SERVER ACCEPT CONNECTION
        response = post_request(
            '{}/sync/environment_resource_operation'.format(addr),
            {'env_uid': 'env1',
             'resource_uid': 'server',
             'res_op': 'accept_connection'}).json()
        _assert_http_response(
            response, 'environment_resource_operation', 'Sync',
            result=0)

        # CLIENT SENDS MESSAGE
        msg = 'Hello world'
        response = post_request(
            '{}/sync/environment_resource_operation'.format(addr),
            {'env_uid': 'env1',
             'resource_uid': 'client',
             'res_op': 'send_text',
             'msg': msg}).json()
        _assert_http_response(
            response, 'environment_resource_operation', 'Sync',
            result=len(msg))

        # SERVER RECEIVES
        response = post_request(
            '{}/sync/environment_resource_operation'.format(addr),
            {'env_uid': 'env1',
             'resource_uid': 'server',
             'res_op': 'receive_text'}).json()
        _assert_http_response(
            response, 'environment_resource_operation', 'Sync',
            result=msg)

        add_second_client_after_environment_started()

        # STOP THE ENVIRONMENT
        response = post_request(
            '{}/sync/stop_environment'.format(addr),
            {'env_uid': 'env1'}).json()
        _assert_http_response(
            response, 'stop_environment', 'Sync',
            result={'client': 'STOPPED', 'client2': 'STOPPED',
                    'server': 'STOPPED'})


def test_reload():
    """Tests reload functionality."""
    import sys
    import inspect
    import subprocess
    import testplan

    testplan_path = os.path.join(
        os.path.dirname(inspect.getfile(testplan)), '..')

    path_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'testplan_path.txt')

    with open(path_file, 'w') as fobj:
        fobj.write(testplan_path)

    subprocess.check_call(
        [sys.executable, 'interactive_executable.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)))
