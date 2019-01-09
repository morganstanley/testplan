import os
import sys
import mock
import time
import json
import socket
from collections import namedtuple

from testplan import Testplan
from testplan.logger import TESTPLAN_LOGGER
from testplan.testing.multitest import MultiTest, testsuite, testcase

from testplan.common.utils.monitor import EventMonitor, ResourceMonitor, load_monitor_from_json
from testplan.common.utils.testing import log_propagation_disabled


class MockData:
    cpu_count = 17
    hostname = 'test_host_name'
    getfqdn = 'test_host_name.example.com'
    time = 19

    @staticmethod
    def virtual_memory():
        virt_mem = namedtuple('svmem',
            ['total', 'available', 'percent', 'used', 'free', 'active', 'inactive', 'buffers', 'cached', 'shared'])
        return virt_mem(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

    @staticmethod
    def disk_usage(path=None):
        disk_used = namedtuple('sdiskusage', ['total', 'used', 'free', 'percent'])
        return disk_used(201, 202, 203, 204)

    @staticmethod
    def memory_info():
        mem_info = namedtuple('pmem', ['rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty'])
        return mem_info(100, 101, 102, 103, 104, 105, 106)

    @staticmethod
    def cpu_percent(interval=0.1):
        return 16

    @staticmethod
    def as_dict(attrs=[]):
        return {
            'cmdline': ['fake', 'cmd'],
            'memory_info': MockData.memory_info(),
            'pid': 107,
            'name': 'mock_python',
            'cpu_percent': MockData.cpu_percent()
        }

    @staticmethod
    def children(recursive=False):
        return []


@mock.patch('time.time', return_value=MockData.time)
@mock.patch('socket.getfqdn', return_value=MockData.getfqdn)
def test_event_started(*args):
    event_monitor = EventMonitor()
    entity_uid = event_monitor.started('mock_event')
    event_monitor.stopped(event_uuid=entity_uid)
    assert event_monitor.hostname == MockData.getfqdn
    assert event_monitor.events_data[entity_uid][0]['time'] == MockData.time
    assert event_monitor.events_data[entity_uid][1]['time'] == MockData.time


@mock.patch('multiprocessing.cpu_count', return_value=MockData.cpu_count)
def test_host_metadata(*args):
    resource_monitor = ResourceMonitor()
    resource_monitor.start()
    assert resource_monitor.host_metadata['num_cpu'] == MockData.cpu_count
    resource_monitor.stop()


@mock.patch('psutil.virtual_memory', side_effect=MockData.virtual_memory)
@mock.patch('psutil.disk_usage', side_effect=MockData.disk_usage)
@mock.patch('psutil.Process.as_dict', side_effect=MockData.as_dict)
@mock.patch('psutil.Process.children', side_effect=MockData.children)
@mock.patch('multiprocessing.cpu_count', return_value=MockData.cpu_count)
def test_resource_polling(*args):
    poll_interval = 1
    timeout = 5
    resource_monitor = ResourceMonitor()
    resource_monitor.poll_interval = poll_interval
    resource_monitor.start()
    time.sleep(timeout)
    resource_monitor.stop()

    mock_memory = MockData.memory_info()
    mock_resource_data = {
        'cpu': MockData.cpu_percent(),
        'memory': mock_memory.rss,
        'disk': MockData.disk_usage().percent
    }
    mock_host_metadata = {
        'num_cpu': MockData.cpu_count,
        'memory': MockData.virtual_memory().total,
        'disk_total': MockData.disk_usage().total,
    }

    for resource, value in mock_resource_data.items():
        assert resource_monitor.monitor_metrics[resource][0] == value

    for meta, value in mock_host_metadata.items():
        assert resource_monitor.host_metadata[meta] == value


@testsuite
class Alpha(object):

    @testcase
    def test_memory_a(self, env, result):
        _tmp = 'testplan' * 1024 * 1024 * (1024 // 8)  # 1GB memory
        time.sleep(10)


def test_resource_monitor():
    plan = Testplan(name='plan', parse_cmdline=False,
                    resource_monitor=True)

    plan.add(MultiTest(name='multitest_x', suites=[Alpha()]))
    with log_propagation_disabled(TESTPLAN_LOGGER):
        plan.run()

    hostname = socket.getfqdn()
    with open(os.path.join(plan.cfg.report_dir, 'monitor.json')) as monitor_file:
        monitor_json = json.load(monitor_file)
    resource_monitor = load_monitor_from_json(monitor_json[hostname])

    assert isinstance(resource_monitor, ResourceMonitor) is True
    big_size = sys.getsizeof('testplan' * 1024 * 1024 * (1024 // 8))
    assert max(resource_monitor.monitor_metrics['memory']) >= big_size

    event_uuid = None
    for uuid, metadata in resource_monitor.events_metadata.items():
        if metadata['name'] == 'multitest_x':
            event_uuid = uuid
    assert event_uuid is not None

    spent_time = resource_monitor.events_data[event_uuid][-1]['time'] - \
                 resource_monitor.events_data[event_uuid][0]['time']
    assert spent_time >= 10
