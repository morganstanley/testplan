"""Child worker process module."""

import argparse
import logging
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback


def parse_cmdline():
    """Child worker command line parsing"""
    parser = argparse.ArgumentParser(description="Remote runner parser")
    parser.add_argument("--address", action="store")
    parser.add_argument("--index", action="store")
    parser.add_argument("--wd", action="store")
    parser.add_argument("--runpath", action="store", default=None)
    parser.add_argument("--type", action="store")
    parser.add_argument("--log-level", action="store", default=0, type=int)
    parser.add_argument("--remote-pool-type", action="store", default="thread")
    parser.add_argument("--remote-pool-size", action="store", default=1)
    parser.add_argument("--sys-path-file", action="store")

    return parser.parse_args()


class ChildLoop:
    """
    Child process loop that can be started in a process and starts a local
    thread pool to execute the tasks received.
    """

    def __init__(
        self,
        index,
        transport,
        pool_type,
        pool_size,
        worker_type,
        logger,
        runpath=None,
    ):
        self._metadata = {"index": index, "pid": os.getpid()}
        self._transport = transport
        self._pool_type = pool_type
        self._pool_size = int(pool_size)
        self._pool_cfg = None
        self._worker_type = worker_type
        self._to_heartbeat = float(0)
        self.runpath = runpath
        self.logger = logger

    @property
    def metadata(self):
        """Metadata information."""
        return self._metadata

    def _child_pool(self):
        # Local thread pool will not cleanup the previous layer runpath.
        self._pool = self._pool_type(
            name=f"Pool_{self._metadata['pid']}",
            worker_type=self._worker_type,
            size=self._pool_size,
            runpath=self.runpath,
            allow_task_rerun=False,  # always return False
        )
        self._pool.parent = self
        self._pool.cfg.parent = self._pool_cfg
        return self._pool

    def _handle_abort(self, signum, frame):
        self.logger.debug(
            "Signal handler called for signal %s from %s",
            signum,
            threading.current_thread(),
        )
        if self._pool:
            self._pool.abort()
            os.kill(os.getpid(), 9)
            self.logger.debug("Pool %s aborted.", self._pool)

    def _setup_logfiles(self):

        from testplan.common.utils.logger import LOGFILE_FORMAT

        if not os.path.exists(self.runpath):
            os.makedirs(self.runpath)

        stdout_file = os.path.join(
            self.runpath, f"{self._metadata['index']}_stdout"
        )
        stderr_file = os.path.join(
            self.runpath, f"{self._metadata['index']}_stderr"
        )
        log_file = os.path.join(self.runpath, f"{self._metadata['index']}_log")
        self.logger.info("stdout file = %s", stdout_file)
        self.logger.info("stderr file = %s", stderr_file)
        self.logger.info(
            "log file = %(file)s (log level = %(lvl)s)",
            {"file": log_file, "lvl": self.logger.level},
        )
        # redirect stdout/stderr
        stderr_fd = open(stderr_file, "w")
        stdout_fd = open(stdout_file, "w")
        os.close(2)
        os.close(1)
        os.dup2(stderr_fd.fileno(), 2)
        os.dup2(stdout_fd.fileno(), 1)

        fhandler = logging.FileHandler(log_file, encoding="utf-8")

        formatter = logging.Formatter(LOGFILE_FORMAT)
        fhandler.setFormatter(formatter)
        fhandler.setLevel(self.logger.level)
        self.logger.addHandler(fhandler)

    def _send_and_expect(self, message, send, expect):
        try:
            return self._transport.send_and_receive(
                message.make(send), expect=expect
            )
        except AttributeError:
            self.logger.critical("Pool seems dead, child exits.")
            raise

    def _pre_loop_setup(self, message):
        response = self._send_and_expect(
            message,
            message.ConfigRequest,
            [message.ConfigSending, message.Stop],
        )

        # Process pool might be exiting after worker restarts and tries
        # to connect, at this time worker can gracefully exit.
        if response.cmd == message.Stop:
            print("Stop message received, child exits.")
            os._exit(0)

        # Response.data: [cfg, cfg.parent, cfg.parent.parent, ...]
        pool_cfg = response.data[0]
        for idx, cfg in enumerate(response.data):
            try:
                cfg.parent = response.data[idx + 1]
            except IndexError:
                break
        self._pool_cfg = pool_cfg

        for sig in self._pool_cfg.abort_signals:
            signal.signal(sig, self._handle_abort)

        pool_metadata = response.sender_metadata

        if self.runpath is None:
            if pool_metadata.get("runpath") is None:
                raise RuntimeError("runpath was not set in pool metadata")
            self.runpath = pool_metadata["runpath"]
        self._setup_logfiles()

    def worker_loop(self):
        """
        Child process worker loop. Manages an underlying thread pool, pulls and
        sends back results to the main pool.
        """
        from testplan.runners.pools.communication import Message

        message = Message(**self.metadata)

        try:
            self._pre_loop_setup(message)
        except Exception:
            print("_pre_loop_setup failed")
            self._transport.send_and_receive(
                message.make(message.SetupFailed, data=traceback.format_exc()),
                expect=message.Ack,
            )
            return

        with self._child_pool():
            message = Message(**self.metadata)
            next_possible_request = 0
            next_heartbeat = 0
            request_delay = self._pool_cfg.active_loop_sleep

            while True:
                # TODO: SHALL CHECK CHILD POOL ALIVE HERE
                now = time.time()

                if self._pool_cfg.worker_heartbeat and now > next_heartbeat:
                    hb_resp = self._transport.send_and_receive(
                        message.make(message.Heartbeat, data=time.time())
                    )
                    if hb_resp is None:
                        self.logger.critical("Pool seems dead, child exits.")
                        self.exit_loop()
                        break
                    else:
                        self.logger.debug(
                            "Pool heartbeat response: %s at %s before %ss.",
                            hb_resp.cmd,
                            hb_resp.data,
                            time.time() - hb_resp.data,
                        )
                    next_heartbeat = now + self._pool_cfg.worker_heartbeat

                # Send back results
                if self._pool.results:
                    task_results = []
                    for uid in list(self._pool.results.keys()):
                        task_results.append(self._pool.results[uid])
                        self.logger.debug(
                            "Sending back result for %s",
                            self._pool.results[uid].task,
                        )
                        del self._pool.results[uid]
                    self._transport.send_and_receive(
                        message.make(message.TaskResults, data=task_results),
                        expect=message.Ack,
                    )

                # Request new tasks
                demand = (
                    self._pool.workers_requests()
                    - self._pool.unassigned.qsize()
                )

                if demand > 0 and time.time() > next_possible_request:
                    received = self._transport.send_and_receive(
                        message.make(message.TaskPullRequest, data=demand)
                    )

                    if received is None or received.cmd == Message.Stop:
                        self.logger.critical(
                            "Pool seems dead or stopping, child exits."
                        )
                        self.exit_loop()
                        break
                    elif received.cmd == Message.TaskSending:
                        next_possible_request = time.time()
                        request_delay = 0
                        for task in received.data:
                            self.logger.debug("Added %s to local pool", task)
                            self._pool.add(task, task.uid())
                        # Reset workers request counters
                        for worker in self._pool._workers:
                            worker.requesting = 0
                    elif received.cmd == Message.Ack:
                        request_delay = min(
                            (request_delay + 0.2) * 1.5,
                            self._pool_cfg.max_active_loop_sleep,
                        )
                        next_possible_request = time.time() + request_delay
                        pass
                time.sleep(self._pool_cfg.active_loop_sleep)
        self.logger.info("Local pool %s stopped.", self._pool)

    def exit_loop(self):
        self._pool.abort()


class RemoteChildLoop(ChildLoop):
    """
    Child loop for remote workers.
    This involved exchange of metadata for additional functionality.
    """

    def __init__(self, *args, **kwargs):
        super(RemoteChildLoop, self).__init__(*args, **kwargs)
        self._setup_metadata = None

    def _pre_loop_setup(self, message):
        super(RemoteChildLoop, self)._pre_loop_setup(message)

        response = self._send_and_expect(
            message, message.MetadataPull, [message.Metadata, message.Stop]
        )

        if response.cmd == message.Stop:
            print("Stop message received, child exits.")
            os._exit(0)

        self._setup_metadata = response.data

        if self._setup_metadata.env:
            for key, value in self._setup_metadata.env.items():
                os.environ[key] = value

        if self._setup_metadata.setup_script:
            if subprocess.call(
                self._setup_metadata.setup_script,
                stdout=sys.stdout,
                stderr=sys.stderr,
            ):
                raise RuntimeError("Setup script exited with non 0 code.")

    def exit_loop(self):
        if self._setup_metadata.delete_pushed:
            for item in self._setup_metadata.push_dirs:
                self.logger.user_info("Removing directory: %s", item)
                shutil.rmtree(item, ignore_errors=True)
            for item in self._setup_metadata.push_files:
                self.logger.user_info("Removing file: %s", item)
                os.remove(item)

        super(RemoteChildLoop, self).exit_loop()


def child_logic(args):
    """Able to be imported child logic."""

    import psutil
    from testplan.runners.pools.base import Pool, Worker
    from testplan.runners.pools.process import ProcessPool, ProcessWorker
    from testplan.runners.pools.connection import ZMQClient

    if args.log_level:
        from testplan.common.utils.logger import (
            TESTPLAN_LOGGER,
            STDOUT_HANDLER,
        )

        TESTPLAN_LOGGER.setLevel(args.log_level)
        TESTPLAN_LOGGER.removeHandler(STDOUT_HANDLER)

    print(
        f"Starting child process worker on {socket.gethostname()},"
        f" {os.getpid()} with parent {psutil.Process(os.getpid()).ppid()}"
    )

    if args.runpath:
        print(f"Removing old runpath: {args.runpath}")
        shutil.rmtree(args.runpath, ignore_errors=True)

    class NoRunpathPool(Pool):
        """
        Pool that creates no runpath directory.
        Has only one worker.
        Will use the one already created by parent process.
        """

        # To eliminate a not needed runpath layer.
        def make_runpath_dirs(self):
            self._runpath = self.cfg.runpath

    class NoRunpathThreadPool(Pool):
        """
        Pool that creates no runpath directory.
        Will use the one already created by parent process.
        Supports multiple thread workers.
        """

        # To eliminate a not needed runpath layer.
        def make_runpath_dirs(self):
            self._runpath = self.cfg.runpath

    class NoRunpathProcessPool(ProcessPool):
        """
        Pool that creates no runpath directory.
        Will use the one already created by parent process.
        Supports multiple process workers.
        """

        # To eliminate a not needed runpath layer.
        def make_runpath_dirs(self):
            self._runpath = self.cfg.runpath

    transport = ZMQClient(address=args.address, recv_timeout=30)

    if args.type == "process_worker":
        loop = ChildLoop(
            args.index, transport, NoRunpathPool, 1, Worker, TESTPLAN_LOGGER
        )
        loop.worker_loop()

    elif args.type == "remote_worker":
        if args.remote_pool_type == "process":
            pool_type = NoRunpathProcessPool
            worker_type = ProcessWorker
        else:
            pool_type = NoRunpathThreadPool
            worker_type = Worker

        loop = RemoteChildLoop(
            args.index,
            transport,
            pool_type,
            args.remote_pool_size,
            worker_type,
            TESTPLAN_LOGGER,
            runpath=args.runpath,
        )
        loop.worker_loop()


def process_syspath_file(filename, working_dir=None):
    """
    Process the syspath file, which should contain one sys.path entry per line
    Since we might be on a remote host, we need to check the accessibility of
    those entries. And we should always be able to directly access modules in
    the working directory. The result is written back to the original file for
    bookkeeping.
    """
    with open(filename) as f:
        new_syspath = f.read().split("\n")
    new_syspath = list(filter(os.path.exists, new_syspath))

    if working_dir is not None:
        new_syspath.insert(0, working_dir)

    with open(filename, "w") as f:
        f.write("\n".join(new_syspath))

    return new_syspath


if __name__ == "__main__":
    """
    To start an external child process worker.
    """
    ARGS = parse_cmdline()
    if ARGS.wd:
        os.chdir(ARGS.wd)
        os.environ["PWD"] = ARGS.wd

    if ARGS.sys_path_file:
        sys.path = process_syspath_file(ARGS.sys_path_file, ARGS.wd)

    # upfront import to speed-up execution
    import testplan
    import psutil
    from testplan.runners.pools.communication import Message
    from testplan.runners.pools.base import Pool, Worker
    from testplan.runners.pools.process import ProcessPool, ProcessWorker
    from testplan.runners.pools.connection import ZMQClient
    from testplan.common.utils.logger import LOGFILE_FORMAT
    from testplan.common.utils.logger import (
        TESTPLAN_LOGGER,
        STDOUT_HANDLER,
    )

    child_logic(ARGS)
    print("child.py exiting")
    os._exit(0)
