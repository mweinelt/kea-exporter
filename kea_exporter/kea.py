import json
import os
import re
import socket
import sys
from enum import Enum

import click
from prometheus_client import Gauge


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


class KeaExporter:
    subnet_pattern = re.compile(
        r"subnet\[(?P<subnet_id>[\d]+)\]\.(?P<metric>[\w-]+)")

    def __init__(self, kea_instances):
        # kea instances
        self.kea_instances = kea_instances

        # prometheus
        self.prefix = 'kea'
        self.prefix_dhcp4 = f'{self.prefix}_dhcp4'
        self.prefix_dhcp6 = f'{self.prefix}_dhcp6'

        self.metrics_dhcp4 = None
        self.metrics_dhcp4_map = None
        self.metrics_dhcp4_ignore = None
        self.setup_dhcp4_metrics()

        self.metrics_dhcp6 = None
        self.metrics_dhcp6_map = None
        self.metrics_dhcp6_ignore = None
        self.setup_dhcp6_metrics()

    def setup_dhcp4_metrics(self):
        self.metrics_dhcp4 = {
            # Packets
            'sent_packets': Gauge(
                f'{self.prefix_dhcp4}_packets_sent_total',
                'Packets sent',
                ['operation']),
            'received_packets': Gauge(
                f'{self.prefix_dhcp4}_packets_received_total',
                'Packets received',
                ['operation']),

            # Allocation
            'allocation_fail': Gauge(
                f'{self.prefix_dhcp4}_allocation_fail_total',
                'Allocation fail count',
                ['allocation']),

            # per Subnet
            'addresses_assigned_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_assigned_total',
                'Assigned addresses',
                ['subnet', 'subnet_id']),
            'addresses_declined_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_declined_total',
                'Declined counts',
                ['subnet', 'subnet_id']),
            'addresses_declined_reclaimed_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_declined_reclaimed_total',
                'Declined addresses that were reclaimed',
                ['subnet', 'subnet_id']),
            'addresses_reclaimed_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_reclaimed_total',
                'Expired addresses that were reclaimed',
                ['subnet', 'subnet_id']),
            'addresses_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_total',
                'Size of subnet address pool',
                ['subnet', 'subnet_id']),
            'reservation_conflicts': Gauge(
                f'{self.prefix_dhcp4}_reservation_conflicts',
                'Reservation conflict count',
                ['subnet', 'subnet_id']),
        }

        self.metrics_dhcp4_map = {
            # sent_packets
            'pkt4-ack-sent': {
                'metric': 'sent_packets',
                'labels': {
                    'operation': 'ack'
                },
            },
            'pkt4-nak-sent': {
                'metric': 'sent_packets',
                'labels': {
                    'operation': 'nak'
                },
            },
            'pkt4-offer-sent': {
                'metric': 'sent_packets',
                'labels': {
                    'operation': 'offer'
                },
            },

            # received_packets
            'pkt4-discover-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'discover'
                }
            },
            'pkt4-offer-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'offer'
                }
            },
            'pkt4-request-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'request'
                }
            },
            'pkt4-ack-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'ack'
                }
            },
            'pkt4-nak-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'nak'
                }
            },
            'pkt4-release-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'release'
                }
            },
            'pkt4-decline-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'decline'
                }
            },
            'pkt4-inform-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'inform'
                }
            },
            'pkt4-unknown-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'unknown'
                }
            },
            'pkt4-parse-failed': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'parse-failed'
                }
            },
            'pkt4-receive-drop': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'drop'
                }
            },

            # Allocation Failed
            'v4-allocation-fail-subnet' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'subnet'
                },
            },

            'v4-allocation-fail-shared-network' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'shared-network'
                },
            },

            'v4-allocation-fail-no-pools' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'no-pools'
                },
            },

            'v4-allocation-fail-classes' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'classes'
                },
            },
   
            # per Subnet
            'assigned-addresses': {
                'metric': 'addresses_assigned_total',
            },
            'declined-addresses': {
                'metric': 'addresses_declined_total',
            },
            'declined-reclaimed-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-declined-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-leases': {
                'metric': 'addresses_reclaimed_total',
            },
            'total-addresses': {
                'metric': 'addresses_total',
            },
            'v4-reservation-conflicts' :{
                'metric' : 'reservation_conflicts',
            }
        }

        self.metrics_dhcp4_ignore = [
            # sums of different packet types
            'v4-reservation-conflicts',
            'v4-allocation-fail',
            'pkt4-sent',
            'pkt4-received',
            # sums of subnet values
            'cumulative-assigned-addresses',
            'declined-addresses',
            'declined-reclaimed-addresses',
            'reclaimed-declined-addresses',
            'reclaimed-leases'
        ]
        # to catch subnet metrics with duplicate names as global metrics
        self.subnet_metric_dhcp4_overide = [
            'v4-reservation-conflicts'
        ]

    def setup_dhcp6_metrics(self):
        self.metrics_dhcp6 = {
            # Packets sent/received
            'sent_packets': Gauge(
                f'{self.prefix_dhcp6}_packets_sent_total',
                'Packets sent',
                ['operation']),
            'received_packets': Gauge(
                f'{self.prefix_dhcp6}_packets_received_total',
                'Packets received',
                ['operation']),

            # Allocation Fail
            'allocation_fail': Gauge(
                f'{self.prefix_dhcp6}_allocation_fail_total',
                'Allocation fail count',
                ['allocation']),

            # DHCPv4-over-DHCPv6
            'sent_dhcp4_packets': Gauge(
                f'{self.prefix_dhcp6}_packets_sent_dhcp4_total',
                'DHCPv4-over-DHCPv6 Packets received',
                ['operation']
            ),
            'received_dhcp4_packets': Gauge(
                f'{self.prefix_dhcp6}_packets_received_dhcp4_total',
                'DHCPv4-over-DHCPv6 Packets received',
                ['operation']
            ),

            # per Subnet
            'addresses_declined_total': Gauge(
                f'{self.prefix_dhcp6}_addresses_declined_total',
                'Declined addresses',
                ['subnet', 'subnet_id']),
            'addresses_declined_reclaimed_total': Gauge(
                f'{self.prefix_dhcp6}_addresses_declined_reclaimed_total',
                'Declined addresses that were reclaimed',
                ['subnet', 'subnet_id']),
            'addresses_reclaimed_total': Gauge(
                f'{self.prefix_dhcp6}_addresses_reclaimed_total',
                'Expired addresses that were reclaimed',
                ['subnet', 'subnet_id']),
            'reservation_conflicts': Gauge(
                f'{self.prefix_dhcp6}_reservation_conflicts',
                'Reservation conflict count',
                ['subnet', 'subnet_id']),

            # IA_NA
            'na_assigned_total': Gauge(
                f'{self.prefix_dhcp6}_na_assigned_total',
                'Assigned non-temporary addresses (IA_NA)',
                ['subnet', 'subnet_id']),
            'na_total': Gauge(
                f'{self.prefix_dhcp6}_na_total',
                'Size of non-temporary address pool',
                ['subnet', 'subnet_id']
            ),

            # IA_PD
            'pd_assigned_total': Gauge(
                f'{self.prefix_dhcp6}_pd_assigned_total',
                'Assigned prefix delegations (IA_PD)',
                ['subnet', 'subnet_id']),
            'pd_total': Gauge(
                f'{self.prefix_dhcp6}_pd_total',
                'Size of prefix delegation pool',
                ['subnet', 'subnet_id']
            ),

        }

        self.metrics_dhcp6_map = {
            # sent_packets
            'pkt6-advertise-sent': {
                'metric': 'sent_packets',
                'labels': {
                    'operation': 'advertise'
                },
            },
            'pkt6-reply-sent': {
                'metric': 'sent_packets',
                'labels': {
                    'operation': 'reply'
                },
            },

            # received_packets
            'pkt6-receive-drop': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'drop'
                },
            },
            'pkt6-parse-failed': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'parse-failed'
                },
            },
            'pkt6-solicit-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'solicit'
                },
            },
            'pkt6-advertise-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'advertise'
                }
            },
            'pkt6-request-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'request'
                }
            },
            'pkt6-reply-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'reply'
                }
            },
            'pkt6-renew-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'renew'
                }
            },
            'pkt6-rebind-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'rebind'
                }
            },
            'pkt6-release-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'release'
                }
            },
            'pkt6-decline-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'decline'
                }
            },
            'pkt6-infrequest-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'infrequest'
                }
            },
            'pkt6-unknown-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'unknown'
                }
            },

            # Allocation Fail 
            'v6-allocation-fail-shared-network' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'shared-network'
                },
            },

            'v6-allocation-fail-subnet' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'subnet'
                },
            },

            'v6-allocation-fail-no-pools' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'no-pools'
                },
            },

            'v6-allocation-fail-classes' :{
                'metric' : 'allocation_fail',
                'labels': {
                    'allocation': 'classes'
                },
            },

            # DHCPv4-over-DHCPv6
            'pkt6-dhcpv4-response-sent': {
                'metric': 'sent_dhcp4_packets',
                'labels': {
                    'operation': 'response'
                }
            },
            'pkt6-dhcpv4-query-received': {
                'metric': 'received_dhcp4_packets',
                'labels': {
                    'operation': 'query'
                }
            },
            'pkt6-dhcpv4-response-received': {
                'metric': 'received_dhcp4_packets',
                'labels': {
                    'operation': 'response'
                }
            },

            # per Subnet
            'assigned-nas': {
                'metric': 'na_assigned_total',
            },
            'assigned-pds': {
                'metric': 'pd_assigned_total',
            },
            'declined-addresses': {
                'metric': 'addresses_declined_total',
            },
            'declined-reclaimed-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-declined-addresses': {
                'metric': 'addresses_declined_reclaimed_total',
            },
            'reclaimed-leases': {
                'metric': 'addresses_reclaimed_total',
            },
            'total-nas': {
                'metric': 'na_total',
            },
            'total-pds': {
                'metric': 'pd_total',
            },
            'v6-reservation-conflicts' :{
                'metric' : 'reservation_conflicts',
            },
        }

        self.metrics_dhcp6_ignore = [
            # sums of different packet types
            'v6-reservation-conflicts',
            'v6-allocation-fail',
            'pkt6-sent',
            'pkt6-received',
            # sums of subnet values
            'cumulative-assigned-nas',
            'cumulative-assigned-pds',
            'declined-addresses',
            'declined-reclaimed-addresses',
            'reclaimed-declined-addresses',
            'reclaimed-leases'
        ]

        # to catch subnet metrics with duplicate names as global metrics
        self.subnet_metric_dhcp6_overide = [
            'v6-reservation-conflicts'
        ]

    def update(self):
        for kea in self.kea_instances:
            for key, data in kea.stats()['arguments'].items():
                if kea.dhcp_version is DHCPVersion.DHCP4:
                    if key in self.metrics_dhcp4_ignore:
                        continue
                elif kea.dhcp_version is DHCPVersion.DHCP6:
                    if key in self.metrics_dhcp6_ignore:
                        continue
                else:
                    continue

                value, timestamp = data[0]
                labels = {}

                # Additional matching is required when we encounter a subnet
                # metric.
                if key.startswith('subnet['):
                    match = self.subnet_pattern.match(key)
                    if match:
                        subnet_id = int(match.group('subnet_id'))
                        key = match.group('metric')

                        if kea.dhcp_version is DHCPVersion.DHCP4:
                            if key in self.metrics_dhcp4_ignore and key not in self.subnet_metric_dhcp4_overide:
                                continue
                        elif kea.dhcp_version is DHCPVersion.DHCP6:
                            if key in self.metrics_dhcp6_ignore and key not in self.subnet_metric_dhcp4_overide:
                                continue
                        else:
                            continue

                        try:
                            subnet = kea.subnets[subnet_id]
                        except KeyError:
                            if subnet_id not in kea.subnet_missing_info_sent:
                                kea.subnet_missing_info_sent.append(subnet_id)
                                click.echo(
                                    f"The subnet with id {subnet_id} on socket {kea.sock_path} appeared in statistics "
                                    f"but is not part of the configuration anymore! Ignoring.",
                                    file=sys.stderr
                                )
                            continue
                        labels['subnet'] = subnet['subnet']
                        labels['subnet_id'] = subnet_id
                    else:
                        click.echo(f'subnet pattern failed for metric: {key}',
                                   file=sys.stderr)

                if kea.dhcp_version is DHCPVersion.DHCP4:
                    metric_info = self.metrics_dhcp4_map[key]
                    metric = self.metrics_dhcp4[metric_info['metric']]
                elif kea.dhcp_version is DHCPVersion.DHCP6:
                    metric_info = self.metrics_dhcp6_map[key]
                    metric = self.metrics_dhcp6[metric_info['metric']]

                # merge static and dynamic labels
                labels.update(metric_info.get('labels', {}))

                # export labels and value
                metric.labels(**labels).set(value)
