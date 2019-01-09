"""Collect system information"""

import os
import time
import platform
import subprocess
import multiprocessing
import psutil


class Collector(object):
    def __init__(self, director):
        self.metadata = {
            'num_cpu': multiprocessing.cpu_count(),
            'memory': psutil.virtual_memory().total,
            'disk_total': psutil.disk_usage(director).total,
            'disk_director': director,
            'system': platform.platform(),
            'extra': {},
        }
        self._pid = os.getpid()

        # save last io counter per process
        self._io_counter = {}

    def monitor(self):
        parent = psutil.Process(self._pid)
        procs = parent.children(recursive=True)
        procs.append(parent)
        monitor_result = {
            'cpu': 0,
            'memory': 0,
            'disk': psutil.disk_usage(self.metadata['disk_director']).percent,
            'iops': 0,
            'read': 0,
            'write': 0,
        }
        for proc in procs:
            try:
                raw_data = proc.as_dict(
                    attrs=['pid', 'name', 'memory_info', 'cpu_percent', 'io_counters', 'create_time', 'io_counters'])

            except psutil.NoSuchProcess:
                continue
            monitor_result['cpu'] += raw_data['cpu_percent'] if raw_data['cpu_percent'] > 0 else 0
            monitor_result['memory'] += raw_data['memory_info'].rss
            try:
                counters = {
                    'io_counter': raw_data['io_counters'].read_count + raw_data['io_counters'].write_count,
                    'read_counter': raw_data['io_counters'].read_bytes,
                    'write_counter': raw_data['io_counters'].write_bytes,
                    'time': time.time()
                }
                iops = read = write = 0
                if raw_data['pid'] in self._io_counter \
                        and self._io_counter[raw_data['pid']]['io_counter'] >= counters['io_counter']:
                    _interval = counters['time'] - self._io_counter[raw_data['pid']]['time']
                    iops = (counters['io_counter'] - self._io_counter[raw_data['pid']]['io_counter']) / _interval
                    read = (counters['read_counter'] - self._io_counter[raw_data['pid']]['read_counter']) / _interval
                    write = (counters['write_counter'] - self._io_counter[raw_data['pid']]['write_counter']) / _interval
                else:
                    _interval = counters['time'] - raw_data['create_time']
                    if _interval >= 1.0:
                        iops = counters['io_counter'] / _interval
                        read = counters['read_counter'] / _interval
                        write = counters['write_counter'] / _interval
                self._io_counter[raw_data['pid']] = counters.copy()
                monitor_result['iops'] += iops
                monitor_result['read'] += read
                monitor_result['write'] += write
            except (AttributeError, KeyError):
                # process exited or no io counters
                pass
        return monitor_result


class LinuxCollector(Collector):
    def __init__(self, director):
        super(LinuxCollector, self).__init__(director)
        try:
            cpu_info = subprocess.check_output(['lscpu'])
            self.metadata['extra']['cpu_info'] = cpu_info.decode()
        except Exception:
            pass


class LinuxContainerCollector(LinuxCollector):
    def __init__(self, director):
        super(LinuxContainerCollector, self).__init__(director)
        with open('/proc/1/cgroup') as cgroup_file:
            for cgroup in cgroup_file:
                try:
                    if ':memory:' in cgroup:
                        path = os.path.join('/sys/fs/cgroup/memory/', cgroup.split(':')[-1][1:],
                                            'memory.limit_in_bytes')
                        with open(path, 'r') as memory_file:
                            self.metadata['memory'] = int(memory_file.read())
                except (IOError, AttributeError, ValueError):
                    pass


class WindowsCollector(Collector):
    def __init__(self, director):
        super(WindowsCollector, self).__init__(director)


def get_collector(director=os.getcwd()):
    if platform.system() == 'Windows':
        return WindowsCollector(director)
    elif platform.system() == 'Linux':
        try:
            with open('/proc/1/cgroup') as cgroup_file:
                for cgroup in cgroup_file:
                    pid, name, group = cgroup.split(':')
                    if group.strip() != '/':
                        return LinuxContainerCollector(director)
        except (IOError, ValueError):
            pass
        return LinuxCollector(director)
    else:
        raise RuntimeError('Unsupported system {}'.format(platform.system()))
