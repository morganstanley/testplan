import os
import json
from testplan import defaults
from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig
from testplan.common.utils.monitor import load_monitor_from_json, ResourceMonitor
from testplan.common.utils.logger import TESTPLAN_LOGGER

from ..base import Exporter


class MonitorExporterConfig(ExporterConfig):
    @classmethod
    def get_options(cls):
        return {
            ConfigOption(
                'report_dir', default=defaults.REPORT_DIR,
                block_propagation=False): str,
            ConfigOption('runpath'): str,
        }


class MonitorExporter(Exporter):
    CONFIG = MonitorExporterConfig

    def export(self, source):
        """
        Read monitor data from each of scratch/monitor/monitor-hostname-uuid.data. Combine the data to
        [
            {
                hostname: hostname1: str
                process: [
                    {
                        pid: pid1,
                        start_time; start_time,
                        stop_time; stop_time,
                        data:  [{
                            thread: thread1:
                            start_time; start_time,
                            stop_time; stop_time,
                            events_data: [
                                [uid1, [{event: start, time: 1234567}, {event: stop, time: 12345678}]],
                                [uid2, [{event: start, time: 1234568}, {event: stop, time: 12345678}]],
                                ...
                            ],
                            events_metadata: {
                                uid1:  {
                                    name: 'multitest1',
                                    passed: true,
                                    type: 'Multitest'
                                }
                            }
                        }, ...]
                    },
                    [pid2: str, start_time stop_time, ...],
                    ...
                ],
                start_time: 1234567,
                stop_time: 12345678,
                host_metadata: {},
                monitor_metrics: {}
            }
            hostname2: {
                ...
            }
        ]
        and order by start time.

        :param source: Exporter instance
        :type source: ``Exporter``

        :return: ``None``
        :rtype: ``NoneType``
        """
        run_path = self.cfg.runpath
        monitor = {}
        path = os.path.join('scratch', 'monitor')
        for dir_path, dir_name, file_names in os.walk(run_path):
            if dir_path.endswith(path) and not dir_name:
                for file_name in file_names:
                    if not file_name.endswith('data'):
                        continue
                    with open(os.path.join(dir_path, file_name)) as event_file:
                        try:
                            serial_json = json.load(event_file)
                            event = load_monitor_from_json(serial_json)
                        except ValueError:
                            # ignore empty file
                            continue
                    if event.hostname not in monitor:
                        monitor[event.hostname] = {
                            'process': {}
                        }
                    if isinstance(event, ResourceMonitor):
                        monitor[event.hostname]['host_metadata'] = event.host_metadata
                        monitor[event.hostname]['monitor_metrics'] = event.monitor_metrics
                    if event.pid not in monitor[event.hostname]['process']:
                        monitor[event.hostname]['process'][event.pid] = {}
                    if event.thread_name not in monitor[event.hostname]['process'][event.pid]:
                        monitor[event.hostname]['process'][event.pid][event.thread_name] = event.to_event_monitor()
                    else:
                        monitor[event.hostname]['process'][event.pid][event.thread_name].attach(
                            event.to_event_monitor()
                        )

        report = []
        for hostname, host_data in monitor.items():
            monitor_host = {
                'hostname': hostname,
                'host_metadata': host_data.get('host_metadata', {}),
                'monitor_metrics': host_data.get('monitor_metrics', {})
            }
            processes = []
            for pid, process_data in host_data['process'].items():
                monitor_process = []
                for thread_name, event_monitor in process_data.items():
                    event_data = event_monitor.dump_data()
                    if event_data['start_time']:
                        monitor_process.append({
                            'thread': thread_name,
                            'start_time': event_data['start_time'],
                            'stop_time': event_data['stop_time'],
                            'data': event_data
                        })
                if monitor_process:
                    monitor_process.sort(key=lambda x: x['start_time'])
                    stop_time = max(monitor_process, key=lambda x: x['stop_time'])['stop_time']
                    processes.append({
                        'pid': pid,
                        'start_time': monitor_process[0]['start_time'],
                        'stop_time': stop_time,
                        'data': monitor_process
                    })
            if processes:
                processes.sort(key=lambda x: x['start_time'])
            monitor_host['process'] = processes
            monitor_host['start_time'] = processes[0]['start_time']
            monitor_host['stop_time'] = max(processes, key=lambda x: x['stop_time'])['stop_time']
            if monitor_host['monitor_metrics'].get('time', []):
                monitor_host['start_time'] = min(monitor_host['start_time'], monitor_host['monitor_metrics']['time'][0])
                monitor_host['stop_time'] = max(monitor_host['stop_time'], monitor_host['monitor_metrics']['time'][-1])
            report.append(monitor_host)
        report.sort(key=lambda x: x['start_time'])
        start_time = min(report, key=lambda x: x['start_time'])['start_time']
        stop_time = max(report, key=lambda x: x['stop_time'])['stop_time']

        file_path = os.path.join(self.cfg.report_dir, 'monitor.json')
        with open(file_path, 'w') as monitor_report:
            json.dump({
                'name': source.name,
                'passed': source.counts.passed,
                'failed': source.counts.failed,
                'start_time': start_time,
                'stop_time': stop_time,
                'data': report,
            }, monitor_report)
        TESTPLAN_LOGGER.exporter_info(
                'Resource monitor generated at {}'.format(file_path))
