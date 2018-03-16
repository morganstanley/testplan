"""Child worker process module."""

import os
import sys
import time
import pickle
import signal
import socket
import argparse
import threading


def parse_cmdline():
    """Child worker command line parsing"""
    parser = argparse.ArgumentParser(description='Remote runner parser')
    parser.add_argument('--address', action="store")
    parser.add_argument('--index', action="store")
    parser.add_argument('--testplan', action="store")
    parser.add_argument('--type', action="store")
    parser.add_argument('--log-level', action="store", default=0, type=int)
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
                except Exception:
                    print('Deserialization error.')
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

    def __init__(self, index, transport, pool_type, worker_type, logger):
        self._metadata = {'index': index, 'pid': os.getpid()}
        self._transport = transport
        self._pool_type = pool_type
        self._worker_type = worker_type
        self._to_heartbeat = float(0)
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

    def _child_pool(self, pool_cfg):
        # Local thread pool will not cleanup the previous layer runpath.
        self._pool = self._pool_type(
            name='Pool_{}'.format(self._metadata['pid']),
            worker_type=self._worker_type, worker_heartbeat=0, size=1,
            runpath=self.runpath, path_cleanup=False)
        self._pool.parent = self
        self._pool.cfg.parent = pool_cfg
        return self._pool

    def _handle_abort(self, signum, frame):
        self.logger.debug('Signal handler called for signal {} from {}'.format(
            signum, threading.current_thread()))
        if self._pool:
            self._pool.abort()
            os.kill(os.getpid(), 9)
            self.logger.debug('Pool {} aborted.'.format(self._pool))

    def worker_loop(self):
        """
        Child process worker loop. Manages an underlying thread pool, pulls and
        sends back results to the main pool.
        """
        from testplan.runners.pools.communication import Message
        message = Message(**self.metadata)

        try:
            response = self._transport.send_and_receive(message.make(
                message.ConfigRequest), expect=message.ConfigSending)
        except AttributeError:
            self.logger.critical('Pool seems dead, child exits.')
        else:
            pool_cfg = response.data

        for sig in pool_cfg.abort_signals:
            signal.signal(sig,  self._handle_abort)

        pool_metadata = response.sender_metadata

        self.runpath = pool_metadata['runpath']

        with self._child_pool(pool_cfg):
            if pool_cfg.worker_heartbeat:
                self.heartbeat_setup()
            message = Message(**self.metadata)
            while True:
                if pool_cfg.worker_heartbeat and self._to_heartbeat <= 0:
                    hb_resp = self._transport.send_and_receive(message.make(
                        message.Heartbeat, data=time.time()))
                    if hb_resp is None:
                        self.logger.critical('Pool seems dead, child exits.')
                        self._pool.abort()
                        break
                    else:
                        self.logger.debug(
                            'Pool heartbeat response:'
                            ' {} at {} before {}s.'.format(
                                hb_resp.cmd, hb_resp.data,
                                time.time() - hb_resp.data))
                    self._to_heartbeat = pool_cfg.worker_heartbeat

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
                if demand > 0:
                    received = self._transport.send_and_receive(message.make(
                        message.TaskPullRequest, data=demand))

                    if received is None or received.cmd == Message.Stop:
                        self.logger.critical('Child exits.')
                        self._pool.abort()
                        break
                    elif received.cmd == Message.TaskSending:
                        for task in received.data:
                            self.logger.debug('Added {} to local pool'.format(
                                task))
                            self._pool.add(task, task.uid())
                        # Reset workers request counters
                        for worker in self._pool._workers:
                            worker.requesting = 0
                    elif received.cmd == Message.Ack:
                        pass
                time.sleep(pool_cfg.active_loop_sleep)
        self.logger.info('Local pool {} stopped.'.format(self._pool))


if __name__ == '__main__':
    """
    To start an external child process worker.
    """
    ARGS = parse_cmdline()
    sys.path.append(ARGS.testplan)

    # This will also import dependencies from $TESTPLAN_DEPENDENCIES_PATH
    import testplan
    if ARGS.log_level:
        from testplan.logger import TESTPLAN_LOGGER
        TESTPLAN_LOGGER.setLevel(ARGS.log_level)

    import psutil
    print('Starting child process worker on {}, {} with parent {}'.format(
        socket.gethostname(), os.getpid(), psutil.Process(os.getpid()).ppid()))

    from testplan.runners.pools.base import Pool, Worker, Transport

    class ChildTransport(ZMQTransport, Transport):
        """Transport that supports message serialization."""

    class NoRunpathPool(Pool):
        """
        Pool that creates no runpath directory.
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
            worker = self.cfg.worker_type(index=ARGS.index,
                                          runpath=self.cfg.runpath)
            self.logger.info('Created {}'.format(worker))
            worker.parent = self
            worker.cfg.parent = self.cfg
            self._workers.add(worker, uid=ARGS.index)
            # print('Added worker with id {}'.format(idx))
            self._conn.register(worker)
            self._workers.start()

    if ARGS.type == 'process_worker':
        transport = ChildTransport(address=ARGS.address)
        loop = ChildLoop(ARGS.index, transport, NoRunpathPool, Worker,
                         TESTPLAN_LOGGER)
        loop.worker_loop()
