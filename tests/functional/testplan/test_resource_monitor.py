import csv
import json
import os
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
    print(f"Runpath: {runpath}")
    current_pid = os.getpid()
    print(f"Current PID: {current_pid}")
    server = ResourceMonitorServer(file_directory=runpath, debug=True)
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
    resource_detail_file_path = (
        server.file_directory / f"{slugify(client.uid)}.debug"
    )
    wait(lambda: meta_file_path.exists(), timeout=client.poll_interval * 2)

    with open(meta_file_path) as meta_file:
        meta_info = json.load(meta_file)
    assert meta_info["uid"] == socket.getfqdn()
    assert meta_info["cpu_count"] == psutil.cpu_count()
    assert meta_info["memory_size"] == psutil.virtual_memory().total
    assert meta_info["disk_path"] == client.disk_path
    assert meta_info["disk_size"] == psutil.disk_usage(client.disk_path).total

    def get_latest_pid_resource_data(pid: int):
        detail = None
        with open(resource_detail_file_path) as resource_detail_file:
            csv_reader = csv.reader(resource_detail_file)
            for line in csv_reader:
                if int(line[1]) == pid:
                    detail = line
        return detail

    def received_resource_data() -> bool:
        if resource_file_path.exists() and resource_detail_file_path.exists():
            with open(resource_file_path) as resource_file:
                csv_reader = csv.reader(resource_file)
                current_pid_data = get_latest_pid_resource_data(current_pid)
                return (
                    len(list(csv_reader)) > 0 and current_pid_data is not None
                )
        return False

    wait(received_resource_data, timeout=client.poll_interval * 2)

    def get_last_resource_data():
        with open(resource_file_path) as resource_file:
            csv_reader = csv.reader(resource_file)
            return list(csv_reader)[-1]

    memory_used = int(get_last_resource_data()[2])
    print(f"Current memory used: {memory_used}")

    current_pid_data = get_latest_pid_resource_data(current_pid)
    print(f"Current PID Data: {current_pid_data}")

    big_memory = ["testplan"] * 1024 * 1024

    def check_pid_memory():
        latest_pid_data = get_latest_pid_resource_data(current_pid)
        if float(latest_pid_data[0]) > float(current_pid_data[0]) and int(
            latest_pid_data[4]
        ) > int(current_pid_data[4]):
            return True
        return False

    wait(check_pid_memory, timeout=client.poll_interval * 4)

    big_memory.clear()

    client.stop()
    server.stop()
