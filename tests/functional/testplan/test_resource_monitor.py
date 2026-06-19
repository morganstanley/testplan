import csv
import dataclasses
import json
import os
import socket
import typing

import psutil

from pytest_test_filters import skip_on_windows
from testplan.monitor.resource import (
    ResourceMonitorServer,
    ResourceMonitorClient,
    HostResourceData,
    HostResourceRow,
    ProcessResourceRow,
)
from testplan.common.utils.strings import slugify
from testplan.common.utils.timing import wait


@dataclasses.dataclass
class _ProbeHostResourceRow(HostResourceRow):
    probe: float = 0.0


@dataclasses.dataclass
class _ProbeHostResourceData(HostResourceData):
    probe: float = 0.0

    def to_row(self, timestamp: float) -> _ProbeHostResourceRow:
        return _ProbeHostResourceRow(
            **dataclasses.asdict(super().to_row(timestamp)), probe=self.probe
        )


class _ProbeResourceMonitorClient(ResourceMonitorClient):
    """Injects an extra typed host metric to exercise the make_host_resource hook."""

    def make_host_resource(self, **base: typing.Any) -> HostResourceData:
        return _ProbeHostResourceData(**base, probe=1.0)


@skip_on_windows(reason="Resource monitor is skipped on Windows.")
def test_resource(runpath):
    print(f"Runpath: {runpath}")
    current_pid = os.getpid()
    print(f"Current PID: {current_pid}")
    server = ResourceMonitorServer(file_directory=runpath, detailed=True)
    assert server.address == ""
    server.start()
    assert server.address != ""
    assert server.file_directory.exists()

    client = _ProbeResourceMonitorClient(server_address=server.address)
    assert client.uid
    assert client.disk_size
    client.poll_interval = 5
    client.start()

    meta_file_path = server.file_directory / f"{slugify(client.uid)}.meta"
    resource_file_path = server.file_directory / f"{slugify(client.uid)}.csv"
    resource_detail_file_path = (
        server.file_directory / f"{slugify(client.uid)}.detailed"
    )
    wait(lambda: meta_file_path.exists(), timeout=client.poll_interval * 2)

    with open(meta_file_path) as meta_file:
        meta_info = json.load(meta_file)
    assert meta_info["uid"] == socket.getfqdn()
    assert meta_info["cpu_count"] == psutil.cpu_count()
    assert meta_info["memory_size"] == psutil.virtual_memory().total
    assert meta_info["disk_path"] == client.disk_path
    assert meta_info["disk_size"] == psutil.disk_usage(client.disk_path).total

    def get_latest_pid_resource_data(
        pid: int,
    ) -> typing.Optional[ProcessResourceRow]:
        detail = None
        with open(resource_detail_file_path) as resource_detail_file:
            csv_reader = csv.reader(resource_detail_file)
            for line in csv_reader:
                _line = ProcessResourceRow(*line)
                if int(_line.pid) == pid:
                    detail = _line
        return detail

    def get_host_rows() -> typing.List[dict]:
        # Host CSV is headered, so read by column name via DictReader.
        with open(resource_file_path, newline="") as resource_file:
            return list(csv.DictReader(resource_file))

    def received_resource_data() -> bool:
        if resource_file_path.exists() and resource_detail_file_path.exists():
            _current_pid_data = get_latest_pid_resource_data(current_pid)
            return len(get_host_rows()) > 0 and _current_pid_data is not None
        return False

    wait(received_resource_data, timeout=client.poll_interval * 2)

    last_host_row = get_host_rows()[-1]
    memory_used = int(float(last_host_row["memory"]))
    print(f"Current memory used: {memory_used}")

    # Core host context-switch rate is collected for every client.
    assert float(last_host_row["host_ctx_switches"]) >= 0
    # Extra typed metric from the HostResourceRow subclass flows through as its
    # own column.
    assert float(last_host_row["probe"]) == 1.0

    current_pid_data = get_latest_pid_resource_data(current_pid)
    print(f"Current PID Data: {current_pid_data}")

    big_memory = ["testplan"] * 1024 * 1024 * 10

    def check_pid_memory():
        latest_pid_data = get_latest_pid_resource_data(current_pid)
        if float(latest_pid_data.timestamp) > float(
            current_pid_data.timestamp
        ) and int(latest_pid_data.memory_used) > int(
            current_pid_data.memory_used
        ):
            return True
        return False

    wait(check_pid_memory, timeout=client.poll_interval * 4)

    big_memory.clear()  # avoid freeing memory early

    meta_path = server.dump()
    with open(meta_path) as meta_file:
        entries = json.load(meta_file)["entries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["time_start"] > 0
    assert entry["time_end"] >= entry["time_start"]
    assert entry["max_cpu"] >= 0
    assert entry["max_memory"] >= 0
    assert entry["max_disk"] >= 0
    assert entry["max_iops"] >= 0
    assert entry["max_system_load"] >= 0
    assert entry["max_host_ctx_switches"] >= 0
    assert entry["max_probe"] == 1.0
    with open(entry["resource_file"]) as resource_file:
        resource_arrays = json.load(resource_file)
    assert resource_arrays["host_ctx_switches"]
    assert resource_arrays["probe"]

    client.stop()
    server.stop()
