"""Resource monitor utilities."""

import os
import uuid
import time
import json
import socket
import logging
import threading
from collections import defaultdict
from testplan.common.utils.logger import Loggable, TESTPLAN_LOGGER
from testplan.common.utils.path import makedirs
from .collectors import get_collector


class EventMonitor(Loggable):
    """
    Event monitor will record event start and stop times(seconds)
    """
    def __init__(self, parent=None):
        super(EventMonitor, self).__init__()
        self.parent = parent
        self.hostname = socket.getfqdn()
        self.events_metadata = {}
        self.events_data = defaultdict(list)
        # The lock protects self.events_metadata
        self.lock = threading.Lock()
        self.log_directory = None
        self.uid = str(uuid.uuid4())
        self.thread_name = threading.current_thread().name
        self.pid = os.getpid()
        self.ppid = os.getppid()

    def attach(self, event_monitor):
        """
        Merge the record event in two EventMonitor

        :param event_monitor:  The EventMonitor will be merged.
        :type event_monitor: ``EventMonitor``
        :return:
        """
        self.events_metadata.update(event_monitor.events_metadata)
        self.events_data.update(event_monitor.events_data)

    def setup_logger(self, log_path=None):
        """
        Sets up a unique logger for Monitor each time it is called. Should only
        be called once or logs will be directed
        to new logger on subsequent call.

        :param log_path: Absolute path to file to save logs to.
        :type log_path: ``str``

        :return: ``None``
        :rtype: ``NoneType``
        """
        if log_path:
            directory = log_path.rsplit(os.sep, 1)[0]
            self.log_directory = directory
            makedirs(directory)
            file_handler = logging.FileHandler(filename=log_path)
        else:
            file_handler = logging.NullHandler()  # pylint: disable=bad-option-value
        formatter = logging.Formatter(
            '%(asctime)s-Monitor-%(levelname)-8s:  %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(TESTPLAN_LOGGER.level)
        self.logger.setLevel(TESTPLAN_LOGGER.level)
        self.logger.addHandler(file_handler)

    def _record_event(self, event_uuid, event):
        self.events_data[event_uuid].append({
            'event': event,
            'time': time.time(),
        })

    def event_started(self, event_type, metadata=None):
        """
        Record event started.

        :param event_type: The type of event. ('Pool', 'Multitest' etc.)
        :type event_type: ``str``
        :param metadata: The properties of the event. ('name', 'pass' etc.)
        :type metadata: ``dict``

        :return: Event unique id
        :rtype: ``str``
        """
        event_uuid = str(uuid.uuid4())
        with self.lock:
            if not metadata:
                _metadata = {}
            elif isinstance(metadata, dict):
                _metadata = metadata.copy()
            else:
                raise TypeError('Event metadata must be a dictionary - not {}'
                                .format(type(metadata)))
            _metadata['type'] = event_type
            self.events_metadata[event_uuid] = _metadata
            self._record_event(event_uuid, 'start')
        return event_uuid

    def event_stopped(self, event_uuid, metadata=None):
        """
        Record event stopped.

        :param event_uuid: Event unique id
        :type event_uuid: ``str``
        :param metadata: The properties of the event want to be updated.

        :return: ``None``
        :rtype: ``NoneType``
        """
        with self.lock:
            if metadata:
                self.events_metadata[event_uuid].update(metadata)
            self._record_event(event_uuid, 'stop')

    def to_dict(self):
        """
        Convert the internal data to a dictionary.

        :return: dict of internal data
        :rtype: ``dict``
        """
        return {
            'events_metadata': self.events_metadata,
            'events_data': dict(self.events_data),
            'hostname': self.hostname,
            'parent': self.parent,
            'thread_name': self.thread_name,
            'ppid': self.ppid,
            'pid': self.pid
        }

    def dump_data(self):
        """
        Convert the event data and metadata to a dictionary. These data are
        sorted by start time.

        :return: dict of internal data
        :rtype: ``dict``
        """
        _result = {
            'events_metadata': self.events_metadata,
            'events_data': [x for x in self.events_data.items()]
        }
        _result['events_data'].sort(key=lambda x: x[1][0]['time'])
        _result['start_time'] = min(
            [x[1][0]['time'] for x in _result['events_data']]) \
            if _result['events_data'] else 0
        _result['stop_time'] = max(
            [x[1][-1]['time'] for x in _result['events_data']]) \
            if _result['events_data'] else 0
        return _result

    def dumps(self):
        """
        Dump the internal data as a JSON string

        :return: JSON string of internal data
        :rtype: ``str``
        """
        return json.dumps(self.to_dict())

    def save(self, scratch_path):
        """
        Save the internal data as a JSON string in file_path. Will append an
        integer to filename
        ensuring it always writes to a new file

        :param scratch_path: file path to save internal data to
        :type scratch_path: ``str``

        :return: ``None``
        :rtype: ``NoneType``
        """
        directory = os.path.join(scratch_path, 'monitor')
        file_name = 'monitor-{}-{}.data'.format(self.hostname, self.uid)
        full_path = os.path.join(directory, file_name)
        if not os.path.exists(directory):
            self.logger.info('Creating directory %s', directory)
            makedirs(directory)
        with open(full_path, 'w') as monitor_file:
            monitor_file.write(self.dumps())
        self.logger.debug('Monitor data saved to {}'.format(full_path))

    def load(self, serial_json):
        """
        Load data from a JSON string or a dict.

        :param serial_json: The json type of event monitor
        :type serial_json: ``str`` or ``dict``

        :return: ``None``
        :rtype: ``NoneType``
        """
        if isinstance(serial_json, str):
            _serial_json = json.loads(serial_json)
        else:
            _serial_json = serial_json
        for name, value in _serial_json.items():
            setattr(self, name, value)
        TESTPLAN_LOGGER.info(
            'Internal data loaded, previous internal data overwritten.')

    def copy(self):
        """
        Create a new EventMonitor instance and copy all attribute to the new
        instance.

        :return: New EventMonitor instance
        :rtype: ``EventMonitor``
        """
        _event_monitor = EventMonitor()
        _event_monitor.hostname = self.hostname
        _event_monitor.pid = self.pid
        _event_monitor.ppid = self.ppid
        _event_monitor.thread_name = self.thread_name
        _event_monitor.events_metadata = self.events_metadata
        _event_monitor.events_data = self.events_data
        return _event_monitor


class ResourceMonitor(EventMonitor):
    """
    Resource Monitor will collect the host hardware information(CPU, memory,
    disk etc.)
    and the metrics(the usage of CPU, memory and disk).

    """

    def __init__(self, directory=None, parent=None, collector=None):
        super(ResourceMonitor, self).__init__(parent=parent)
        self._collector = collector or get_collector(directory)
        self._poll = None
        self._poll_event = threading.Event()
        self._poll_start = False
        self.poll_interval = 2
        self.host_metadata = self._collector.metadata
        self.monitor_metrics = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'iops': [],
            'read': [],
            'write': [],
            'time': []
        }

    def _monitoring(self):
        while self._poll_start:
            _now = time.time()
            _metrics = self._collector.monitor()
            _metrics['time'] = _now
            for key in self.monitor_metrics.keys():
                self.monitor_metrics[key].append(_metrics[key])

            _sleep_time = self.poll_interval - (time.time() - _now)
            if _sleep_time > 0:
                time.sleep(_sleep_time)

    def start(self):
        """
        Start the thread of collect the metrics.

        :return: ``None``
        :rtype: ``NoneType``
        """
        self._poll = threading.Thread(target=self._monitoring)
        self._poll.daemon = True
        self._poll_start = True
        self._poll.start()
        TESTPLAN_LOGGER.info('Resource polling started.')

    def stop(self):
        """
        Stop collect metrics.

        :return: ``None``
        :rtype: ``NoneType``
        """
        if self._poll:
            self._poll_start = False
            self._poll.join()
            self._poll = None
            TESTPLAN_LOGGER.info('Resource polling stopped.')

    def to_dict(self):
        _result = super(ResourceMonitor, self).to_dict()
        _result['host_metadata'] = self.host_metadata
        _result['monitor_metrics'] = self.monitor_metrics
        return _result


def load_monitor_from_json(serial_json):
    """
    Convert JSON string to EventMonitor/ResourceMonitor object

    :param serial_json:
    :type serial_json: ``str`` or ``dict``

    :return: the instance of EventMonitor/ResourceMonitor
    :rtype: ``EventMonitor`` or ``ResourceMonitor``
    """
    if isinstance(serial_json, str):
        _serial_json = json.loads(serial_json)
    else:
        _serial_json = serial_json
    if 'host_metadata' in _serial_json:
        event_monitor = ResourceMonitor()
    else:
        event_monitor = EventMonitor()
    event_monitor.load(_serial_json)
    return event_monitor
