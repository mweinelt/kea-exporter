import json
import os
import socket
import sys

import click

from .base_exporter import BaseExporter

class KeaSocket:
    def __init__(self, sock_path):
        try:
            if not os.access(sock_path, os.F_OK):
                raise FileNotFoundError()
            if not os.access(sock_path, os.R_OK | os.W_OK):
                raise PermissionError()
            self.sock_path = os.path.abspath(sock_path)
        except FileNotFoundError:
            click.echo(f'Socket at {sock_path} does not exist. Is Kea running?', file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            click.echo(f'Socket at {sock_path} is not read-/writeable.', file=sys.stderr)
            sys.exit(1)

        self.version = None
        self.config = None
        self.subnets = None
        self.subnet_missing_info_sent = []
        self.dhcp_version = None

    def query(self, command):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(self.sock_path)
            sock.send(bytes(json.dumps({'command': command}), 'utf-8'))
            response = json.loads(sock.makefile().read(-1))

        if response['result'] != 0:
            raise ValueError

        return response

    def stats(self):
        # I don't currently know how to detect a changed configuration, so
        # unfortunately we're reloading more often now as a workaround.
        self.reload()

        return self.query('statistic-get-all')

    def reload(self):
        self.config = self.query('config-get')['arguments']

        if 'Dhcp4' in self.config:
            self.dhcp_version = BaseExporter.DHCPVersion.DHCP4
            subnets = self.config['Dhcp4']['subnet4']
        elif 'Dhcp6' in self.config:
            self.dhcp_version = BaseExporter.DHCPVersion.DHCP6
            subnets = self.config['Dhcp6']['subnet6']
        else:
            click.echo(f'Socket {self.sock_path} has no supported configuration', file=sys.stderr)
            sys.exit(1)

        # create subnet map
        self.subnets = {subnet['id']: subnet for subnet in subnets}


class KeaSocketExporter(BaseExporter):
    def __init__(self, sockets, **kwargs):
        super().__init__()
        
        # kea instances
        self.kea_instances = [KeaSocket(socket) for socket in sockets]


    def update(self):
        for kea in self.kea_instances:
            kea.dhcp_version
            self.parse_metrics(kea.dhcp_version, kea.stats().get('arguments'), kea.subnets)
