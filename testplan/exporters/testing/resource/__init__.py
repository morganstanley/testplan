
import os
import json
from testplan import defaults
from testplan.common.config import ConfigOption
from testplan.common.exporters import ExporterConfig
from testplan.common.utils.monitor import load_monitor_from_json
from testplan.logger import TESTPLAN_LOGGER

from ..base import Exporter


class ResourceExporterConfig(ExporterConfig):
    @classmethod
    def get_options(cls):
        return {
            ConfigOption(
                'report_dir', default=defaults.REPORT_DIR,
                block_propagation=False): str
        }


class ResourceExporter(Exporter):
    CONFIG = ResourceExporterConfig

    def export(self, source):
        run_path = self.cfg.runpath
        host_event = {}
        path = os.path.join('scratch', 'monitor')
        for dir_path, dir_name, file_names in os.walk(run_path):
            if dir_path.endswith(path) and not dir_name:
                for file_name in file_names:
                    with open(os.path.join(dir_path, file_name)) as event_file:
                        serial_json = json.load(event_file)
                    event_monitor = load_monitor_from_json(serial_json)
                    if event_monitor.hostname in host_event:
                        if hasattr(event_monitor, 'host_metadata'):
                            event_monitor.attach(host_event[event_monitor.hostname])
                            host_event[event_monitor.hostname] = event_monitor
                        else:
                            host_event[event_monitor.hostname].attach(event_monitor)
                    else:
                        host_event[event_monitor.hostname] = event_monitor
        report_content = {}
        for host, event in host_event.items():
            report_content[host] = event.to_dict()

        file_path = os.path.join(self.cfg.report_dir, 'monitor.json')
        with open(file_path, 'w') as monitor_report:
            json.dump(report_content, monitor_report)
        TESTPLAN_LOGGER.exporter_info(
                'Resource monitor generated at {}'.format(file_path))
