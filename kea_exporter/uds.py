import json
import os
import socket
import sys

import click

from kea_exporter import DHCPVersion


class KeaSocketClient:
    def __init__(self, sock_path, **kwargs):
        super().__init__()

        if not os.access(sock_path, os.F_OK):
            raise FileNotFoundError(f"Unix domain socket does not exist at {sock_path}")
        if not os.access(sock_path, os.R_OK | os.W_OK):
            raise PermissionError(f"No read/write permissions on Unix domain socket at {sock_path}")

        self.sock_path = os.path.abspath(sock_path)

        self.version = None
        self.config = None
        self.subnets = None
        self.subnet_missing_info_sent = []
        self.dhcp_version = None

    def query(self, command):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(self.sock_path)
            sock.send(bytes(json.dumps({"command": command}), "utf-8"))
            response = json.loads(sock.makefile().read(-1))

        if response["result"] != 0:
            raise ValueError

        return response

    def stats(self):
        # I don't currently know how to detect a changed configuration, so
        # unfortunately we're reloading more often now as a workaround.
        self.reload()

        arguments = self.query("statistic-get-all").get("arguments", {})

        yield self.dhcp_version, arguments, self.subnets

    def reload(self):
        self.config = self.query("config-get")["arguments"]

        if "Dhcp4" in self.config:
            self.dhcp_version = DHCPVersion.DHCP4
            subnets = self.config["Dhcp4"]["subnet4"]
        elif "Dhcp6" in self.config:
            self.dhcp_version = DHCPVersion.DHCP6
            subnets = self.config["Dhcp6"]["subnet6"]
        else:
            click.echo(
                f"Socket {self.sock_path} has no supported configuration",
                file=sys.stderr,
            )
            sys.exit(1)

        # create subnet map
        self.subnets = {subnet["id"]: subnet for subnet in subnets}
