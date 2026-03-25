import os
import csv
import time
import socket
import pathlib
import asyncio
import logging
import dataclasses

import zmq
import zmq.asyncio
import psutil
import multiprocessing

from typing import Any, Dict, List, Optional, Union, TextIO, NamedTuple
from testplan.defaults import RESOURCE_META_FILE_NAME
from testplan.common.utils.observability import tracing, otel_logging
from testplan.common.utils.path import pwd
from testplan.common.utils.json import json_dumps, json_loads
from testplan.common.utils.strings import slugify
from testplan.common.utils.logger import LOGFILE_FORMAT
from testplan.common.utils.timing import wait
from testplan.runners.pools import communication
from testplan.common.serialization.base import serialize, deserialize


@dataclasses.dataclass
class ResourceData:
    """
    Attributes of collecting resource data
    """

    cpu_usage: float
    memory_used: int
    iops: float
    io_read: float
    io_write: float


@dataclasses.dataclass
class HostResourceData(ResourceData):
    """
    Host level resource data
    """

    disk_used: int
    system_load: float


@dataclasses.dataclass
class ProcessResourceData(ResourceData):
    """
    Process level resource data
    """

    name: str
    cmdline: str
    pid: int


class HostResourceRow(NamedTuple):
    """
    CSV file row structure of host level resource
    """

    timestamp: float
    cpu_usage: float
    memory_used: int
    disk_used: int
    iops: float
    io_read: float
    io_write: float
    system_load: float


class ProcessResourceRow(NamedTuple):
    """
    CSV file row structure of process level resource
    """

    timestamp: float
    pid: int
    name: str
    cpu_usage: float
    memory_used: int
    iops: float
    io_read: float
    io_write: float
    cmdline: str


class ResourceMonitorClient:
    def __init__(
        self,
        server_address: str,
        disk_path: Optional[str] = None,
        is_local: bool = False,
    ) -> None:
        """
        Client for collecting resource data and sending them to Resource Monitor Server.

        :param server_address: ZMQ binding address, e.g. tcp://127.0.0.1:8888.
        :param disk_path: Directory to measure disk space.
        """
        self.server_address: str = server_address
        self.parent_pid: int = os.getpid()
        self.uid: Optional[str] = None
        self.cpu_count: int = 0
        self.memory_size: int = 0
        self.hostname: str = socket.gethostname()
        self.disk_path: str = disk_path or pwd()
        self.disk_size: int = 0
        self.is_local: bool = is_local
        self.enrich_metadata()

        self.last_host_resource: Optional[HostResourceData] = None
        self.last_process_resource: Dict[int, ProcessResourceData] = {}

        self.last_host_io_info: Dict[str, int] = {}
        self.last_process_io_info: Dict[int, Dict[str, int]] = {}

        self.last_poll_time: float = 0
        self.poll_interval: int = 5
        self.parent_process: Optional[psutil.Process] = None
        self._monitor_worker: Optional[multiprocessing.Process] = None
        self._zmq_context: Optional[zmq.Context] = None
        self._zmq_socket: Optional[zmq.Socket] = None

    def enrich_metadata(self) -> None:
        """
        Enrich host hardware info
        """
        self.uid = socket.getfqdn()
        self.cpu_count = psutil.cpu_count()
        self.memory_size = psutil.virtual_memory().total
        self.disk_size = psutil.disk_usage(self.disk_path).total

    def send_metadata(self) -> None:
        msg = communication.Message(uid=self.uid)
        msg.make(
            cmd=communication.Message.Metadata,
            data={
                "uid": self.uid,
                "hostname": self.hostname,
                "cpu_count": self.cpu_count,
                "memory_size": self.memory_size,
                "disk_path": self.disk_path,
                "disk_size": self.disk_size,
                "is_local": self.is_local,
            },
        )
        self.zmq_socket.send(serialize(msg))

    def collect_cpu_usage(self) -> float:
        return psutil.cpu_percent(0.1)  # type: ignore[no-any-return]

    def collect_memory_usage(self) -> int:
        return self.memory_size - psutil.virtual_memory().available  # type: ignore[no-any-return]

    @staticmethod
    def _ensure_positive(num: float) -> float:
        # Fix IO counter issue
        return max(num, 0)

    def collect_host_data(self) -> None:
        _disk_io = psutil.disk_io_counters()
        iops = _disk_io.read_count + _disk_io.write_count
        io_read = _disk_io.read_bytes
        io_write = _disk_io.write_bytes
        if self.last_host_io_info:
            iops = self._ensure_positive(
                (iops - self.last_host_io_info["iops"]) / self.poll_interval
            )
            io_read = self._ensure_positive(
                (io_read - self.last_host_io_info["io_read"])
                / self.poll_interval
            )
            io_write = self._ensure_positive(
                (io_write - self.last_host_io_info["io_write"])
                / self.poll_interval
            )
            host_resource = HostResourceData(
                cpu_usage=self.collect_cpu_usage(),
                memory_used=self.collect_memory_usage(),
                disk_used=psutil.disk_usage(self.disk_path).used,
                iops=iops,
                io_read=io_read,
                io_write=io_write,
                system_load=psutil.getloadavg()[0],
            )
            self.last_host_resource = host_resource

        self.last_host_io_info = {
            "iops": _disk_io.read_count + _disk_io.write_count,
            "io_read": _disk_io.read_bytes,
            "io_write": _disk_io.write_bytes,
        }

    def collect_process_data(self) -> None:
        if self.parent_process is None:
            raise RuntimeError("self.parent_process must not be None")
        processes = self.parent_process.children(recursive=True)
        processes.append(self.parent_process)
        # Prime cpu_percent for all processes (first call always returns 0.0)
        for proc in processes:
            try:
                proc.cpu_percent()
            except psutil.NoSuchProcess:
                continue

        # Short sleep to allow CPU measurement interval
        time.sleep(0.1)

        self.last_process_resource = {}
        for proc in processes:
            try:
                raw_data = proc.as_dict(
                    attrs=[
                        "pid",
                        "name",
                        "memory_info",
                        "cpu_percent",
                        "cmdline",
                        "io_counters",
                        "create_time",
                    ]
                )
            except psutil.NoSuchProcess:
                continue
            cpu_percent = float(raw_data["cpu_percent"])
            if cpu_percent < 0:
                cpu_percent = 0.0
            iops: float = 0
            io_read: float = 0
            io_write: float = 0
            try:
                counters = {
                    "iops": raw_data["io_counters"].read_count
                    + raw_data["io_counters"].write_count,
                    "io_read": raw_data["io_counters"].read_bytes,
                    "io_write": raw_data["io_counters"].write_bytes,
                }
                if proc.pid in self.last_process_io_info:
                    _pid_last_io = self.last_process_io_info[raw_data["pid"]]
                    iops = self._ensure_positive(
                        (counters["iops"] - _pid_last_io["io_counter"])
                        / self.poll_interval
                    )
                    io_read = self._ensure_positive(
                        (counters["io_read"] - _pid_last_io["read_counter"])
                        / self.poll_interval
                    )
                    io_write = self._ensure_positive(
                        (counters["io_write"] - _pid_last_io["write_counter"])
                        / self.poll_interval
                    )
                else:
                    iops = counters["iops"] / self.poll_interval
                    io_read = counters["io_read"] / self.poll_interval
                    io_write = counters["io_write"] / self.poll_interval
                self.last_process_io_info[proc.pid] = counters.copy()
            except (AttributeError, KeyError):
                # process exited or no io counters
                pass
            self.last_process_resource[proc.pid] = ProcessResourceData(
                name=raw_data["name"],
                cmdline=raw_data["cmdline"],
                pid=proc.pid,
                cpu_usage=cpu_percent,
                memory_used=raw_data["memory_info"].rss,
                iops=iops,
                io_read=io_read,
                io_write=io_write,
            )

    def collect_data(self) -> None:
        self.collect_host_data()
        self.collect_process_data()

    def send_data(self) -> None:
        if self.last_host_resource:
            msg = communication.Message(uid=self.uid)
            msg.make(
                cmd=communication.Message.Message,
                data={
                    "time": self.last_poll_time,
                    "host_resource": self.last_host_resource,
                    "process_resource": self.last_process_resource,
                },
            )
            self.zmq_socket.send(serialize(msg))

    def _loop(self) -> None:
        self.parent_process = psutil.Process(pid=self.parent_pid)
        self._zmq_context = zmq.Context()
        self.zmq_socket = self._zmq_context.socket(zmq.PUSH)
        self.zmq_socket.connect(self.server_address)
        self.send_metadata()
        start_time = time.time()
        poll_index = 0
        while True:
            poll_index += 1
            self.last_poll_time = time.time()
            self.collect_data()
            self.send_data()
            rest_time = (
                start_time + self.poll_interval * poll_index - time.time()
            )
            if rest_time > 0:
                time.sleep(rest_time)

    def start(self) -> None:
        tracing.force_flush()  # flush so that no grpc communication is happening while forking
        otel_logging.force_flush()
        self._monitor_worker = multiprocessing.Process(
            target=self._loop, daemon=True
        )
        self._monitor_worker.start()

    def stop(self) -> None:
        if self._monitor_worker:
            try:
                self._monitor_worker.kill()
                self._monitor_worker.join()
            except:
                pass
            self._monitor_worker = None


class ResourceMonitorServer:
    def __init__(
        self, file_directory: Union[str, pathlib.Path], detailed: bool = False
    ) -> None:
        """
        Start a ZMQ server for receiving resource data from client.

        :param file_directory: Directory path for saving resource data and log.
        :param detailed: Save resource data for per process if detailed is True.
        """
        self.file_directory = pathlib.Path(file_directory)
        self.detailed = detailed
        self._file_handler: Dict[str, Dict[str, Any]] = {}
        self._server_process: Optional[multiprocessing.Process] = None
        self.collector_server: str = socket.getfqdn()
        self.collector_port: int = 0
        self.active_loop_sleep: int = 30
        self._address: str = ""
        self.logger: logging.Logger = logging.getLogger(
            self.__class__.__name__
        )
        self.logger.setLevel(logging.INFO)
        self._zmq_context: Optional[zmq.asyncio.Context] = None
        self._zmq_socket: Optional[zmq.asyncio.Socket] = None

    @property
    def address(self) -> str:
        return self._address

    async def handle_request(self, msg: bytes) -> None:
        message: communication.Message = deserialize(msg)
        client_id: str = message.sender_metadata["uid"]
        if message.cmd == communication.Message.Metadata:
            self.logger.info("Received meta data from %s.", client_id)
            with open(
                self.file_directory / f"{slugify(client_id)}.meta", "w"
            ) as f:
                f.write(json_dumps(message.data))
        elif message.cmd == communication.Message.Message:
            self.logger.info("Received resource data from %s.", client_id)
            if client_id not in self._file_handler:
                self._file_handler[client_id] = {}
                self._file_handler[client_id]["host_file"] = open(
                    self.file_directory / f"{slugify(client_id)}.csv", "w"
                )
                self._file_handler[client_id]["host_csv"] = csv.writer(
                    self._file_handler[client_id]["host_file"]
                )
            client_host_data: HostResourceData = message.data["host_resource"]
            row = HostResourceRow(
                message.data["time"],
                client_host_data.cpu_usage,
                client_host_data.memory_used,
                client_host_data.disk_used,
                client_host_data.iops,
                client_host_data.io_read,
                client_host_data.io_write,
                client_host_data.system_load,
            )
            self._file_handler[client_id]["host_csv"].writerow(row)
            self._file_handler[client_id]["host_file"].flush()
            if self.detailed:
                process_data: Dict[int, ProcessResourceData] = message.data[
                    "process_resource"
                ]
                if "detailed_file" not in self._file_handler[client_id]:
                    self._file_handler[client_id]["detailed_file"] = open(
                        self.file_directory / f"{slugify(client_id)}.detailed",
                        "w",
                    )
                    self._file_handler[client_id]["detailed_csv"] = csv.writer(
                        self._file_handler[client_id]["detailed_file"]
                    )
                for pid, process in process_data.items():
                    detail_row = ProcessResourceRow(
                        message.data["time"],
                        pid,
                        process.name,
                        process.cpu_usage,
                        process.memory_used,
                        process.iops,
                        process.io_read,
                        process.io_write,
                        process.cmdline,
                    )
                    self._file_handler[client_id]["detailed_csv"].writerow(
                        detail_row
                    )
                self._file_handler[client_id]["detailed_file"].flush()
        else:
            self.logger.info(
                "Received unknown data cmd %s, ignored!", message.cmd
            )

    async def collector_service(self) -> None:
        if self._zmq_socket is None:
            raise RuntimeError("self._zmq_socket must not be None")
        while True:
            msg = await self._zmq_socket.recv_multipart()
            for m in msg:
                await self.handle_request(m)

    def _serve(self, shared_dict: Dict[str, Any]) -> None:
        # setup log
        fhandler = logging.FileHandler(
            self.file_directory / "resource.log", encoding="utf-8"
        )
        formatter = logging.Formatter(LOGFILE_FORMAT)
        fhandler.setFormatter(formatter)
        fhandler.setLevel(self.logger.level)
        self.logger.addHandler(fhandler)
        self.logger.info("Starting resource monitor server!")

        self._zmq_context = zmq.asyncio.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.PULL)
        self.collector_port = self._zmq_socket.bind_to_random_port(
            "tcp://0.0.0.0"
        )
        shared_dict["collector_port"] = self.collector_port
        self.logger.info("Resource monitor server started!")
        self.logger.info(
            "Listening port %d, PID: %d!", self.collector_port, os.getpid()
        )
        asyncio.run(self.collector_service())

    def normalize_data(self, client_id: str) -> Optional[Dict[str, Any]]:
        try:
            client_host_path = (
                self.file_directory / f"{slugify(client_id)}.csv"
            )
            resource_data: Dict[str, List[Any]] = {
                "time": [],
                "cpu": [],
                "memory": [],
                "disk": [],
                "iops": [],
                "io_read": [],
                "io_write": [],
                "system_load": [],
            }
            with open(client_host_path) as client_file:
                reader = csv.reader(client_file)
                for row in reader:
                    host_resource = HostResourceRow(*row)  # type: ignore[arg-type]
                    resource_data["time"].append(
                        float(host_resource.timestamp)
                    )
                    resource_data["cpu"].append(float(host_resource.cpu_usage))
                    resource_data["memory"].append(
                        float(host_resource.memory_used)
                    )
                    resource_data["disk"].append(int(host_resource.disk_used))
                    resource_data["iops"].append(float(host_resource.iops))
                    resource_data["io_read"].append(
                        float(host_resource.io_read)
                    )
                    resource_data["io_write"].append(
                        float(host_resource.io_write)
                    )
                    resource_data["system_load"].append(
                        float(host_resource.system_load)
                    )
            json_file_path = self.file_directory / f"{slugify(client_id)}.json"
            with open(json_file_path, "w") as json_file:
                json_file.write(json_dumps(resource_data))
            return {
                "resource_file": str(json_file_path.resolve()),
                "time_start": min(resource_data["time"]),
                "time_end": max(resource_data["time"]),
                "max_cpu": max(resource_data["cpu"]),
                "max_memory": max(resource_data["memory"]),
                "max_disk": max(resource_data["disk"]),
                "max_iops": max(resource_data["iops"]),
                "max_system_load": max(resource_data["system_load"]),
            }
        except FileNotFoundError:
            return None

    def dump(self) -> str:
        resource_info: List[Any] = []
        for host_meta_path in self.file_directory.glob("*.meta"):
            with open(host_meta_path) as meta_file:
                meta = json_loads(meta_file.read())
            summary_data = self.normalize_data(meta["uid"])
            if summary_data:
                meta.update(summary_data)
            if meta["is_local"]:
                resource_info.insert(0, meta)
            else:
                resource_info.append(meta)
        meta_file_path = self.file_directory / RESOURCE_META_FILE_NAME
        with open(meta_file_path, "w") as meta_file:
            meta_file.write(json_dumps({"entries": resource_info}))
        return str(meta_file_path.resolve())

    def start(self, timeout: int = 5) -> None:
        shared_dict = multiprocessing.Manager().dict()
        tracing.force_flush()  # flush so that no grpc communication is happening while forking
        otel_logging.force_flush()
        self._server_process = multiprocessing.Process(
            target=self._serve, args=(shared_dict,), daemon=True
        )
        self._server_process.start()

        def is_started() -> bool:
            return shared_dict.get("collector_port") is not None

        wait(is_started, timeout=timeout)
        self.collector_port = shared_dict["collector_port"]
        self._address = f"tcp://{self.collector_server}:{self.collector_port}"

    def stop(self) -> None:
        if self._server_process:
            try:
                self._server_process.kill()
                self._server_process.join()
            except:  # Handle potential race condition during process termination
                pass
            self._server_process = None
            self._address = ""
            self.collector_port = 0
