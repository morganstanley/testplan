import math
import mock
import time

from testplan.common.utils.monitor import ResourceMonitor
from testplan.common.utils.monitor.collectors import WindowsCollector


class MockData(object):
    @staticmethod
    def fake_getfqdn():
        return 'fake_hostname'

    @staticmethod
    def fake_pid():
        return 10

    @staticmethod
    def fake_ppid():
        return 1

    @staticmethod
    def fake_system():
        return 'Windows'


class TestMonitor(object):

    @mock.patch('socket.getfqdn', side_effect=MockData.fake_getfqdn)
    @mock.patch('os.getpid', side_effect=MockData.fake_pid)
    @mock.patch('os.getppid', side_effect=MockData.fake_ppid)
    def test_host_info(self, *args):
        monitor = ResourceMonitor()
        assert monitor.hostname == MockData.fake_getfqdn()
        assert monitor.pid == MockData.fake_pid()
        assert monitor.ppid == MockData.fake_ppid()

    def test_monitor_thread(self):
        monitor = ResourceMonitor()
        monitor.poll_interval = 5
        monitor.start()
        assert monitor._poll.is_alive() is True
        start_time = math.ceil(time.time())
        monitor.stop()
        stop_time = math.floor(time.time())
        assert stop_time - start_time <= monitor.poll_interval

    @mock.patch('platform.system', side_effect=MockData.fake_system)
    def test_collector(self, *args):
        monitor = ResourceMonitor()
        assert isinstance(monitor._collector, WindowsCollector) is True

    def test_dump(self):
        monitor = ResourceMonitor()
        monitor.start()
        time.sleep(2*monitor.poll_interval)
        monitor.stop()
        metric_data = monitor.to_dict()['monitor_metrics']
        for key in ('cpu', 'memory', 'disk'):
            assert len(metric_data[key]) >= 1
        new_monitor = ResourceMonitor()
        new_monitor.load(monitor.dumps())

        assert new_monitor.pid == monitor.pid
        assert new_monitor.ppid == monitor.ppid
        assert new_monitor.parent == monitor.parent
        assert new_monitor.hostname == monitor.hostname
        assert new_monitor.thread_name == monitor.thread_name
        assert new_monitor.events_data == monitor.events_data
        assert new_monitor.events_metadata == monitor.events_metadata

        assert new_monitor.host_metadata == monitor.host_metadata
        assert new_monitor.monitor_metrics == monitor.monitor_metrics
