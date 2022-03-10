"""
Converter application that:

    1. Connects to an external service that provides FX exchange rates.
    2. Accepts requests from clients i.e: 1000 GBP to be converted to EUR
    3. Requests the currency rate from the FX rates service. i.e: 1.15
    4. Responds to the client with the converted amount: i.e: 1150
"""

import os
import re
import sys
import socket
import logging

from configparser import ConfigParser


logging.basicConfig(stream=sys.stdout, format="%(message)s")


class FXConverter:
    """FXConverter class that accepts a config file."""

    def __init__(self, config_file):
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.INFO)
        self._config = self.load_config(
            os.path.join(os.getcwd(), "etc", config_file)
        )
        self._server = None

    def load_config(self, filename):
        """
        Reads from the config file the host/port information of the downstream
        service and also the host/port to bind and listen for clients.
        """
        config = ConfigParser()
        config.read(filename)

        self._logger.info("Configuration read:")
        for section in ("Listener", "Downstream"):
            self._logger.info(section)
            self._logger.info("\tHost: {}".format(config.get(section, "Host")))
            self._logger.info("\tPort: {}".format(config.get(section, "Port")))
        return config

    def _server_init(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind(
            (
                self._config.get("Listener", "Host"),
                int(self._config.get("Listener", "Port")),
            )
        )
        self._server.listen(10)
        return self._server.getsockname()

    def _validate_request(self, msg):
        if not re.match(r"[A-Z]{3}:[A-Z]{3}:[0-9]+", msg):
            raise ValueError("Invalid request format ({}).".format(msg))

    def _process_request(self, downstream_cli, msg):
        value = float(msg[8:])  # i.e 1000
        if value == 0:
            return "0"
        currencies = msg[:7]  # i.e EUR:GBP
        source, target = currencies.split(":")
        if source == target:
            rate = 1
        else:
            downstream_cli.sendall(bytes(currencies.encode("utf-8")))
            rate = float(downstream_cli.recv(1024).decode("utf-8"))
        result = str(int(rate * value))
        self._logger.info(
            "Request result for {} with rate {}: {}".format(
                msg[8:], rate, result
            )
        )
        return result

    def _loop(self, upstream_conn, downstream_cli, downstream_addr):
        while True:
            msg = str(upstream_conn.recv(1024).decode("utf-8"))
            self._logger.info("Client msg: {}".format(msg))
            if msg == "Stop":
                self._server.close()
                self._logger.info("Converter stopped.")
                break
            else:
                try:
                    self._validate_request(msg)
                except Exception as exc:
                    upstream_conn.sendall(bytes(str(exc).encode("utf-8")))
                    continue
                else:
                    self._logger.info(
                        "Propagating query {} to {}".format(
                            msg, downstream_addr
                        )
                    )

                result = self._process_request(downstream_cli, msg)
                upstream_conn.sendall(bytes(result.encode("utf-8")))

    def loop(self):
        """
        Starts the application.

            1. Connect to downstream server with FX exchange rates.
            2. Accepts client connection.
            3. Start the loop to handle client requests.
        """
        host, port = self._server_init()
        self._logger.info("Listener on: {}:{}".format(host, port))
        downstream_addr = (
            self._config.get("Downstream", "Host"),
            int(self._config.get("Downstream", "Port")),
        )
        self._logger.info(
            "Connected to downstream: {}:{}".format(
                downstream_addr[0], downstream_addr[1]
            )
        )
        downstream_cli = socket.create_connection(downstream_addr)
        self._logger.info("Converter started.")
        upstream_conn, client_address = self._server.accept()
        self._logger.info("Client connected: {}".format(client_address))
        self._loop(upstream_conn, downstream_cli, downstream_addr)


if __name__ == "__main__":
    sys.stderr.flush()
    _, config_file = sys.argv
    converter = FXConverter(config_file)
    converter.loop()
