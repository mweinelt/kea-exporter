import json
import logging
import os
import socket
import sys

from kea_exporter import DHCPVersion

logger = logging.getLogger(__name__)


class KeaSocketClient:
    def __init__(self, sock_path, **kwargs):
        super().__init__()

        if not os.access(sock_path, os.F_OK):
            raise FileNotFoundError(f"Unix domain socket does not exist at {sock_path}")
        if not os.access(sock_path, os.R_OK | os.W_OK):
            raise PermissionError(f"No read/write permissions on Unix domain socket at {sock_path}")

        self.sock_path = os.path.abspath(sock_path)

        self.subnets = None
        self.server_tag = ""
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

        yield self.sock_path, self.server_tag, self.dhcp_version, arguments, self.subnets

    def reload(self):
        config = self.query("config-get").get("arguments", {})

        if "Dhcp4" in config:
            self.dhcp_version = DHCPVersion.DHCP4
            subnets = config.get("Dhcp4", {}).get("subnet4", [])
            self.server_tag = config.get("Dhcp4", {}).get("server-tag", "")
        elif "Dhcp6" in config:
            self.dhcp_version = DHCPVersion.DHCP6
            subnets = config.get("Dhcp6", {}).get("subnet6", [])
            self.server_tag = config.get("Dhcp6", {}).get("server-tag", "")
        else:
            logging.error(
                f"Socket {self.sock_path} has no supported configuration",
            )
            sys.exit(1)
        self.subnets = subnets
