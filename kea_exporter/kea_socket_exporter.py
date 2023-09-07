import json
import os
import socket
import sys

from enum import Enum

import click

from .base_exporter import BaseExporter

class DHCPVersion(Enum):
    DHCP4 = 1
    DHCP6 = 2

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
            self.dhcp_version = DHCPVersion.DHCP4
            subnets = self.config['Dhcp4']['subnet4']
        elif 'Dhcp6' in self.config:
            self.dhcp_version = DHCPVersion.DHCP6
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
            for key, data in kea.stats()['arguments'].items():
                if kea.dhcp_version is DHCPVersion.DHCP4:
                    if key in self.metrics_dhcp4_global_ignore:
                        continue
                elif kea.dhcp_version is DHCPVersion.DHCP6:
                    if key in self.metrics_dhcp6_global_ignore:
                        continue
                else:
                    continue

                value, _ = data[0]
                labels = {}

                # Additional matching is required when we encounter a subnet
                # metric.
                subnet_match = self.subnet_pattern.match(key)
                if subnet_match:
                    subnet_id = int(subnet_match.group('subnet_id'))
                    pool_index = subnet_match.group('pool_index')
                    pool_metric = subnet_match.group('pool_metric')
                    subnet_metric = subnet_match.group('subnet_metric')

                    if kea.dhcp_version is DHCPVersion.DHCP4:
                        if key in self.metric_dhcp4_subnet_ignore:
                            continue
                    elif kea.dhcp_version is DHCPVersion.DHCP6:
                        if key in self.metric_dhcp6_subnet_ignore:
                            continue
                    else:
                        continue

                    try:
                        subnet_data = kea.subnets[subnet_id]
                    except KeyError:
                        if subnet_id not in kea.subnet_missing_info_sent:
                            kea.subnet_missing_info_sent.append(subnet_id)
                            click.echo(
                                f"The subnet with id {subnet_id} on socket {kea.sock_path} appeared in statistics "
                                f"but is not part of the configuration anymore! Ignoring.",
                                file=sys.stderr
                            )
                        continue
                    
                    labels['subnet'] = subnet_data.get('subnet')
                    labels['subnet_id'] = subnet_id

                    # Check if subnet matches the pool_index
                    if pool_index:
                        # Matched for subnet pool metrics
                        pool_index = int(pool_index)
                        subnet_pools = subnet_data.get("pools", [])
                        
                        if len(subnet_pools) <= pool_index:
                            if f"{subnet_id}-{pool_index}" not in kea.subnet_missing_info_sent:
                                kea.subnet_missing_info_sent.append(f"{subnet_id}-{pool_index}")
                                click.echo(
                                    f"The subnet with id {subnet_id} and pool_index {pool_index} on socket {kea.sock_path} appeared in statistics "
                                    f"but is not part of the configuration anymore! Ignoring.",
                                    file=sys.stderr
                                )
                            continue
                        key = pool_metric
                        labels["pool"] = subnet_pools[pool_index]
                    else:
                        # Matched for subnet metrics
                        key = subnet_metric
                        labels["pool"] = ""

                if kea.dhcp_version is DHCPVersion.DHCP4:
                    metrics_map = self.metrics_dhcp4_map
                    metrics = self.metrics_dhcp4
                elif kea.dhcp_version is DHCPVersion.DHCP6:
                    metrics_map = self.metrics_dhcp6_map
                    metrics = self.metrics_dhcp6
                else:
                    continue

                try:
                    metric_info = metrics_map[key]
                except KeyError:
                    if key not in self.unhandled_metrics:
                        click.echo(f"Unhandled metric '{key}', please open an issue at https://github.com/mweinelt/kea-exporter/issues")
                        self.unhandled_metrics.add(key)
                    continue
                metric = metrics[metric_info['metric']]

                # merge static and dynamic labels
                labels.update(metric_info.get('labels', {}))

                # Filter labels that are not configured for the metric
                labels = {key: val for key, val in labels.items() if key in metric._labelnames}

                # export labels and value
                metric.labels(**labels).set(value)
