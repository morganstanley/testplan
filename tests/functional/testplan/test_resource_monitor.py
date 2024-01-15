import csv
import json
import socket
import psutil

from pytest_test_filters import skip_on_windows
from testplan.monitor.resource import (
    ResourceMonitorServer,
    ResourceMonitorClient,
)
from testplan.common.utils.strings import slugify
from testplan.common.utils.timing import wait


@skip_on_windows(reason="Resource monitor is skipped on Windows.")
def test_resource(runpath):
    server = ResourceMonitorServer(file_directory=runpath)
    assert server.address == ""
    server.start()
    assert server.address != ""
    assert server.file_directory.exists()

    client = ResourceMonitorClient(server_address=server.address)
    assert client.uid
    assert client.disk_size
    client.poll_interval = 5
    client.start()

    meta_file_path = server.file_directory / f"{slugify(client.uid)}.meta"
    resource_file_path = server.file_directory / f"{slugify(client.uid)}.csv"
    wait(lambda: meta_file_path.exists(), timeout=client.poll_interval)

    with open(meta_file_path) as meta_file:
        meta_info = json.load(meta_file)
    assert meta_info["uid"] == socket.getfqdn()
    assert meta_info["cpu_count"] == psutil.cpu_count()
    assert meta_info["memory_size"] == psutil.virtual_memory().total
    assert meta_info["disk_path"] == client.disk_path
    assert meta_info["disk_size"] == psutil.disk_usage(client.disk_path).total

    def received_resource_data() -> bool:
        if resource_file_path.exists():
            with open(resource_file_path) as resource_file:
                csv_reader = csv.reader(resource_file)
                return len(list(csv_reader)) > 0
        return False

    wait(received_resource_data, timeout=client.poll_interval)

    def get_last_resource_data():
        with open(resource_file_path) as resource_file:
            csv_reader = csv.reader(resource_file)
            return list(csv_reader)[-1]

    memory_used = get_last_resource_data()[2]

    big_memory = ["testplan"] * 1024 * 1024

    def check_memory():
        last_data = get_last_resource_data()
        if last_data[2] > memory_used:
            return True
        return False

    wait(check_memory, timeout=client.poll_interval * 2)

    big_memory.clear()

    client.stop()
    server.stop()
