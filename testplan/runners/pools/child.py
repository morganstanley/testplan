"""Child worker process module."""

import os
import sys
import time
import pickle
import signal
import socket
import shutil
import inspect
import logging
import argparse
import platform
import threading
import subprocess


def parse_cmdline():
    """Child worker command line parsing"""
    parser = argparse.ArgumentParser(description='Remote runner parser')
    parser.add_argument('--address', action="store")
    parser.add_argument('--index', action="store")
    parser.add_argument('--testplan', action="store")
    parser.add_argument('--testplan-deps', action="store", default=None)
    parser.add_argument('--wd', action="store")
    parser.add_argument('--runpath', action="store", default=None)
    parser.add_argument('--type', action="store")
    parser.add_argument('--log-level', action="store", default=0, type=int)
    parser.add_argument('--remote-pool-type', action="store", default='thread')
    parser.add_argument('--remote-pool-size', action="store", default=1)

    return parser.parse_args()


class ZMQTransport(object):
    """
    Transport layer for communication between a pool and child process worker.
    Worker send serializable messages, pool receives and send back responses.

    :param address: Pool address to connect to.
    :type address: ``float``
    :param recv_sleep: Sleep duration in msg receive loop.
    :type recv_sleep: ``float``
    """

    def __init__(self, address, recv_sleep=0.05, recv_timeout=5):
        import zmq
        self._zmq = zmq
        self._recv_sleep = recv_sleep
        self._recv_timeout = recv_timeout
        self._context = zmq.Context()
        self._sock = self._context.socket(zmq.REQ)
        self._sock.connect("tcp://{}".format(address))
        self.active = True
        self.logger = logging.getLogger(self.__class__.__name__)

    def send(self, message):
        """
        Worker sends a message.

        :param message: Message to be sent.
        :type message: :py:class:`~testplan.runners.pools.communication.Message`
        """
        self._sock.send(pickle.dumps(message))

    def receive(self):
        """
        Worker receives the response to the message sent.

        :return: Response to the message sent.
        :type: :py:class:`~testplan.runners.pools.communication.Message`
        """
        start_time = time.time()
        while self.active:
            try:
                received = self._sock.recv(flags=self._zmq.NOBLOCK)
                try:
                    loaded = pickle.loads(received)
                except Exception as exc:
                    print('Deserialization error. - {}'.format(exc))
                    raise
                else:
                    return loaded
            except self._zmq.Again:
                if time.time() - start_time > self._recv_timeout:
                    print('Transport receive timeout {}s reached!'.format(
                        self._recv_timeout))
                    return None
                time.sleep(self._recv_sleep)
        return None


class ChildLoop(object):
    """
    Child process loop that can be started in a process and starts a local
    thread pool to execute the tasks received.
    """

    def __init__(self, index, transport, pool_type, pool_size,
                 worker_type, logger, runpath=None):
        self._metadata = {'index': index, 'pid': os.getpid()}
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

    def heartbeat_thread(self):
        """Manage a variable that indicates the sending of next heartbeat."""
        while self._pool.status.tag == self._pool.STATUS.STARTED:
            if self._to_heartbeat > 0:
                sleep_interval = max(float(self._to_heartbeat)/2, 0.1)
                self._to_heartbeat -= sleep_interval
                time.sleep(sleep_interval)
            else:
                time.sleep(0.1)

    def heartbeat_setup(self):
        """Start the heartbeat manager thread."""
        heartbeat = threading.Thread(target=self.heartbeat_thread,)
        heartbeat.daemon = True
        heartbeat.start()

    def _child_pool(self):
        # Local thread pool will not cleanup the previous layer runpath.
        self._pool = self._pool_type(
            name='Pool_{}'.format(self._metadata['pid']),
            worker_type=self._worker_type,
            size=self._pool_size,
            runpath=self.runpath)
        self._pool.parent = self
        self._pool.cfg.parent = self._pool_cfg
        return self._pool

    def _handle_abort(self, signum, frame):
        self.logger.debug('Signal handler called for signal {} from {}'.format(
            signum, threading.current_thread()))
        if self._pool:
            self._pool.abort()
            os.kill(os.getpid(), 9)
            self.logger.debug('Pool {} aborted.'.format(self._pool))

    def _setup_logfiles(self):
        if not os.path.exists(self.runpath):
            os.makedirs(self.runpath)

        stderr_file = os.path.join(self.runpath, '{}_stderr'.format(self._metadata['index']))
        log_file = os.path.join(self.runpath, '{}_stdout'.format(self._metadata['index']))
        self.logger.info('stdout file = %(file)s (log level = %(lvl)s)',
                         {'file': log_file, 'lvl': self.logger.level})
        self.logger.info('stderr file = %s'.format(stderr_file))
        self.logger.info(
            'Closing stdin, stdout and stderr file descriptors...')

        # This closes stdin, stdout and stderr for this process.
        for fdesc in range(3):
            os.close(fdesc)
        mode = 'w' if platform.python_version().startswith('3') else 'wb'

        sys.stderr = open(stderr_file, mode)
        fhandler = logging.FileHandler(log_file)
        fhandler.setLevel(self.logger.level)
        self.logger.addHandler = fhandler

    def _send_and_expect(self, message, send, expect):
        try:
            return self._transport.send_and_receive(message.make(
                send), expect=expect)
        except AttributeError:
            self.logger.critical('Pool seems dead, child exits.')
            raise

    def _pre_loop_setup(self, message):
        response = self._send_and_expect(
            message, message.ConfigRequest, message.ConfigSending)

        # Response.data: [cfg, cfg.parent, cfg.parent.parent, ...]
        pool_cfg = response.data[0]
        for idx, cfg in enumerate(response.data):
            try:
                cfg.parent = response.data[idx + 1]
                print(cfg.parent)
            except IndexError:
                break
        self._pool_cfg = pool_cfg

        for sig in self._pool_cfg.abort_signals:
            signal.signal(sig,  self._handle_abort)

        pool_metadata = response.sender_metadata

        self.runpath = self.runpath or str(pool_metadata['runpath'])
        self._setup_logfiles()

    def worker_loop(self):
        """
        Child process worker loop. Manages an underlying thread pool, pulls and
        sends back results to the main pool.
        """
        from testplan.runners.pools.communication import Message
        from testplan.common.utils.exceptions import format_trace
        message = Message(**self.metadata)

        try:
            self._pre_loop_setup(message)
        except Exception as exc:
            self._transport.send_and_receive(message.make(
                message.SetupFailed,
                data=format_trace(inspect.trace(), exc)), expect=message.Ack)
            return

        with self._child_pool():
            if self._pool_cfg.worker_heartbeat:
                self.heartbeat_setup()
            message = Message(**self.metadata)
            next_possible_request = time.time()
            request_delay = self._pool_cfg.active_loop_sleep
            while True:
                if self._pool_cfg.worker_heartbeat and self._to_heartbeat <= 0:
                    hb_resp = self._transport.send_and_receive(message.make(
                        message.Heartbeat, data=time.time()))
                    if hb_resp is None:
                        self.logger.critical('Pool seems dead, child exits.')
                        self.exit_loop()
                        break
                    else:
                        self.logger.debug(
                            'Pool heartbeat response:'
                            ' {} at {} before {}s.'.format(
                                hb_resp.cmd, hb_resp.data,
                                time.time() - hb_resp.data))
                    self._to_heartbeat = self._pool_cfg.worker_heartbeat

                # Send back results
                if self._pool.results:
                    task_results = []
                    for uid in list(self._pool.results.keys()):
                        task_results.append(self._pool.results[uid])
                        self.logger.debug('Sending back result for {}'.format(
                            self._pool.results[uid].task))
                        del self._pool.results[uid]
                    self._transport.send_and_receive(message.make(
                        message.TaskResults,
                        data=task_results), expect=message.Ack)

                # Request new tasks
                demand = self._pool.workers_requests() -\
                         len(self._pool.unassigned)

                if demand > 0 and time.time() > next_possible_request:
                    received = self._transport.send_and_receive(message.make(
                        message.TaskPullRequest, data=demand))

                    if received is None or received.cmd == Message.Stop:
                        self.logger.critical('Child exits.')
                        self.exit_loop()
                        break
                    elif received.cmd == Message.TaskSending:
                        next_possible_request = time.time()
                        request_delay = 0
                        for task in received.data:
                            self.logger.debug('Added {} to local pool'.format(
                                task))
                            self._pool.add(task, task.uid())
                        # Reset workers request counters
                        for worker in self._pool._workers:
                            worker.requesting = 0
                    elif received.cmd == Message.Ack:
                        request_delay = min(
                            (request_delay + 0.2) * 1.5,
                            self._pool_cfg.max_active_loop_sleep)
                        next_possible_request = time.time() + request_delay
                        pass
                time.sleep(self._pool_cfg.active_loop_sleep)
        self.logger.info('Local pool {} stopped.'.format(self._pool))

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
        self._setup_metadata = self._send_and_expect(
            message, message.MetadataPull, message.Metadata).data

        if self._setup_metadata.env:
            for key, value in self._setup_metadata.env.items():
                os.environ[key] = value
        os.environ['TESTPLAN_LOCAL_WORKSPACE'] = \
            self._setup_metadata.workspace_paths.local
        os.environ['TESTPLAN_REMOTE_WORKSPACE'] = \
            self._setup_metadata.workspace_paths.remote
        if self._setup_metadata.push_dir:
            os.environ['TESTPLAN_PUSH_DIR'] = self._setup_metadata.push_dir

        if self._setup_metadata.setup_script:
            if subprocess.call(self._setup_metadata.setup_script,
                               stdout=sys.stdout, stderr=sys.stderr):
                raise RuntimeError('Setup script exited with non 0 code.')

    def exit_loop(self):
        if self._pool.cfg.delete_pushed:
            for item in self._setup_metadata.push_dirs:
                self.logger.test_info('Removing directory: {}'.format(item))
                shutil.rmtree(item, ignore_errors=True)
            for item in self._setup_metadata.push_files:
                self.logger.test_info('Removing file: {}'.format(item))
                os.remove(item)
            # Only delete the source workspace if it was transferred.
            if self._setup_metadata.workspace_pushed is True:
                self.logger.test_info('Removing workspace: {}'.format(
                    self._setup_metadata.workspace_paths.remote))
                shutil.rmtree(self._setup_metadata.workspace_paths.remote,
                              ignore_errors=True)
        super(RemoteChildLoop, self).exit_loop()


def child_logic(args):
    """Able to be imported child logic."""
    if args.log_level:
        from testplan.logger import TESTPLAN_LOGGER
        TESTPLAN_LOGGER.setLevel(args.log_level)

    import psutil
    print('Starting child process worker on {}, {} with parent {}'.format(
        socket.gethostname(), os.getpid(), psutil.Process(os.getpid()).ppid()))

    if args.runpath:
        print('Removing old runpath: {}'.format(args.runpath))
        shutil.rmtree(args.runpath, ignore_errors=True)

    from testplan.runners.pools.base import (
        Pool, Worker, Transport)
    from testplan.runners.pools.process import (
        ProcessPool, ProcessWorker, ProcessTransport)

    class ChildTransport(ZMQTransport, Transport):
        """Transport that supports message serialization."""

    class NoRunpathPool(Pool):
        """
        Pool that creates no runpath directory.
        Has only one worker.
        Will use the one already created by parent process.
        """
        # To eliminate a not needed runpath layer.
        def make_runpath_dirs(self):
            self._runpath = self.cfg.runpath

        def starting(self):
            super(Pool, self).starting()
            self.make_runpath_dirs()

            self._metadata['runpath'] = self.runpath

            # Create a local thread worker with the process pool index
            worker = self.cfg.worker_type(index=args.index,
                                          runpath=self.cfg.runpath)
            self.logger.info('Created {}'.format(worker))
            worker.parent = self
            worker.cfg.parent = self.cfg
            self._workers.add(worker, uid=args.index)
            # print('Added worker with id {}'.format(idx))
            self._conn.register(worker)
            self._workers.start()

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

    if args.type == 'process_worker':
        transport = ChildTransport(address=args.address)
        loop = ChildLoop(args.index, transport, NoRunpathPool, 1, Worker,
                         TESTPLAN_LOGGER)
        loop.worker_loop()

    elif args.type == 'remote_worker':
        if args.remote_pool_type == 'process':
            pool_type = NoRunpathProcessPool
            worker_type = ProcessWorker
        else:
            pool_type = NoRunpathThreadPool
            worker_type = Worker
        transport = ChildTransport(address=args.address)

        loop = RemoteChildLoop(
            args.index, transport, pool_type, args.remote_pool_size,
            worker_type, TESTPLAN_LOGGER, runpath=args.runpath)
        loop.worker_loop()


if __name__ == '__main__':
    """
    To start an external child process worker.
    """
    ARGS = parse_cmdline()
    if ARGS.wd:
        os.chdir(ARGS.wd)
        sys.path.insert(0, ARGS.wd)

    sys.path.append(ARGS.testplan)
    if ARGS.testplan_deps:
        sys.path.append(ARGS.testplan_deps)
    try:
        import dependencies
        # This will also import dependencies from $TESTPLAN_DEPENDENCIES_PATH
    except ImportError:
        pass

    import testplan
    if ARGS.testplan_deps:
        os.environ[testplan.TESTPLAN_DEPENDENCIES_PATH] = ARGS.testplan_deps

    child_logic(ARGS)
