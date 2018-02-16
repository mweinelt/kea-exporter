import os
import re
import socket
import sys
from enum import Enum

import click
import hjson as json
import inotify.adapters
import inotify.constants
from prometheus_client import Gauge


class Module(Enum):
    DHCP4 = 1
    DHCP6 = 2


class KeaExporter:
    subnet_pattern = re.compile(
        r"subnet\[(?P<subnet_idx>[\d]+)\]\.(?P<metric>[\w-]+)")

    msg_statistics_all = bytes(
        json.dumpsJSON({'command': 'statistic-get-all'}), 'utf-8')

    def __init__(self, config_path):
        # kea control socket
        self.sock_dhcp6 = None
        self.sock_dhcp6_path = None
        self.sock_dhcp4 = None
        self.sock_dhcp4_path = None

        # prometheus
        self.prefix = 'kea'
        self.prefix_dhcp4 = '{0}_dhcp4'.format(self.prefix)
        self.prefix_dhcp6 = '{0}_dhcp6'.format(self.prefix)

        self.metrics_dhcp4 = None
        self.metrics_dhcp4_map = None
        self.metrics_dhcp4_ignore = None
        self.setup_dhcp4_metrics()

        self.metrics_dhcp6 = None
        self.metrics_dhcp6_map = None
        self.metrics_dhcp6_ignore = None
        self.setup_dhcp6_metrics()

        # kea config
        self.config_path = config_path
        self.config = None

        self.inotify = inotify.adapters.Inotify()
        self.inotify.add_watch(
            config_path, mask=inotify.constants.IN_MODIFY
        )

        self.load_config()

    def load_config(self):
        with open(self.config_path, 'r') as handle:
            self.config = json.load(handle)

        try:
            sock_path = self.config['Dhcp4']['control-socket']['socket-name']
            if not os.access(sock_path, os.F_OK):
                raise FileNotFoundError()
            if not os.access(sock_path, os.R_OK | os.W_OK):
                raise PermissionError()
            self.sock_dhcp4_path = sock_path
        except KeyError:
            click.echo('Dhcp4.control-socket.socket-name not configured, '
                       'will not be exporting Dhcp4 metrics', file=sys.stderr)
        except FileNotFoundError:
            click.echo('Dhcp4 control-socket configured, but it does not '
                       'exist. Is Kea running?', file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            click.echo('Dhcp4 control-socket is not read-/writeable.',
                       file=sys.stderr)
            sys.exit(1)

        try:
            sock_path = self.config['Dhcp6']['control-socket']['socket-name']
            if not os.access(sock_path, os.F_OK):
                raise FileNotFoundError()
            if not os.access(sock_path, os.R_OK | os.W_OK):
                raise PermissionError()
            self.sock_dhcp6_path = sock_path
        except KeyError:
            click.echo('Dhcp6.control-socket.socket-name not configured, '
                       'will not be exporting Dhcp6 metrics', file=sys.stderr)
        except FileNotFoundError:
            click.echo('Dhcp6 control-socket configured, but it does not '
                       'exist. Is Kea running?', file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            click.echo('Dhcp6 control-socket is not read-/writeable.',
                       file=sys.stderr)
            sys.exit(1)

    def setup_dhcp4_metrics(self):
        self.metrics_dhcp4 = {
            # Packets
            'sent_packets': Gauge(
                '{0}_packets_sent_total'.format(self.prefix_dhcp4),
                'Packets sent',
                ['operation']),
            'received_packets': Gauge(
                '{0}_packets_received_total'.format(self.prefix_dhcp4),
                'Packets received',
                ['operation']),

            # per Subnet
            'addresses_assigned_total': Gauge(
                '{0}_addresses_assigned_total'.format(self.prefix_dhcp4),
                'Assigned addresses',
                ['subnet']),
            'addresses_declined_total': Gauge(
                '{0}_addresses_declined_total'.format(self.prefix_dhcp4),
                'Declined counts',
                ['subnet']),
            'addresses_declined_reclaimed_total': Gauge(
                '{0}_addresses_declined_reclaimed_total'.format(
                    self.prefix_dhcp4),
                'Declined addresses that were reclaimed',
                ['subnet']),
            'addresses_reclaimed_total': Gauge(
                '{0}_addresses_reclaimed_total'.format(self.prefix_dhcp4),
                'Expired addresses that were reclaimed',
                ['subnet']),
            'addresses_total': Gauge(
                '{0}_addresses_total'.format(self.prefix_dhcp4),
                'Size of subnet address pool',
                ['subnet']
            )
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
            }
        }

        self.metrics_dhcp4_ignore = [
            # sums of different packet types
            'pkt4-sent',
            'pkt4-received',
            # sums of subnet values
            'declined-addresses',
            'declined-reclaimed-addresses',
            'reclaimed-declined-addresses',
            'reclaimed-leases'
        ]

    def setup_dhcp6_metrics(self):
        self.metrics_dhcp6 = {
            # Packets sent/received
            'sent_packets': Gauge(
                '{0}_packets_sent_total'.format(self.prefix_dhcp6),
                'Packets sent',
                ['operation']),
            'received_packets': Gauge(
                '{0}_packets_received_total'.format(self.prefix_dhcp6),
                'Packets received',
                ['operation']),

            # DHCPv4-over-DHCPv6
            'sent_dhcp4_packets': Gauge(
                '{0}_packets_sent_dhcp4_total'.format(self.prefix_dhcp6),
                'DHCPv4-over-DHCPv6 Packets received',
                ['operation']
            ),
            'received_dhcp4_packets': Gauge(
                '{0}_packets_received_dhcp4_total'.format(self.prefix_dhcp6),
                'DHCPv4-over-DHCPv6 Packets received',
                ['operation']
            ),

            # per Subnet
            'addresses_declined_total': Gauge(
                '{0}_addresses_declined_total'.format(self.prefix_dhcp6),
                'Declined addresses',
                ['subnet']),
            'addresses_declined_reclaimed_total': Gauge(
                '{0}_addresses_declined_reclaimed_total'.format(
                    self.prefix_dhcp6),
                'Declined addresses that were reclaimed',
                ['subnet']),
            'addresses_reclaimed_total': Gauge(
                '{0}_addresses_reclaimed_total'.format(self.prefix_dhcp6),
                'Expired addresses that were reclaimed',
                ['subnet']),

            # IA_NA
            'na_assigned_total': Gauge(
                '{0}_na_assigned_total'.format(self.prefix_dhcp6),
                'Assigned non-temporary addresses (IA_NA)',
                ['subnet']),
            'na_total': Gauge(
                '{0}_na_total'.format(self.prefix_dhcp6),
                'Size of non-temporary address pool',
                ['subnet']
            ),

            # IA_PD
            'pd_assigned_total': Gauge(
                '{0}_pd_assigned_total'.format(self.prefix_dhcp6),
                'Assigned prefix delegations (IA_PD)',
                ['subnet']),
            'pd_total': Gauge(
                '{0}_pd_total'.format(self.prefix_dhcp6),
                'Size of prefix delegation pool',
                ['subnet']
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
                'metric': 'receoved_packets',
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
            }
        }

        self.metrics_dhcp6_ignore = [
            # sums of different packet types
            'pkt6-sent',
            'pkt6-received',
            # sums of subnet values
            'declined-addresses',
            'declined-reclaimed-addresses',
            'reclaimed-declined-addresses',
            'reclaimed-leases'
        ]

    def update(self):
        reload_config = False
        for event in self.inotify.event_gen():
            if not event:
                break
            reload_config = True

        if reload_config:
            click.echo('Config was modified, reloading...', file=sys.stderr)
            self.load_config()

        for sock_path, module in [(self.sock_dhcp4_path, Module.DHCP4),
                                  (self.sock_dhcp6_path, Module.DHCP6)]:
            if sock_path is None:
                continue

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(sock_path)
                sock.send(KeaExporter.msg_statistics_all)
                response = sock.recv(8192).decode()
                self.parse_metrics(json.loads(response), module)

    def parse_metrics(self, response, module):
        for key, data in response['arguments'].items():
            if module is Module.DHCP4:
                if key in self.metrics_dhcp4_ignore:
                    continue
            else:
                if key in self.metrics_dhcp6_ignore:
                    continue

            value, timestamp = data[0]
            labels = {}

            # lookup subnet
            if key.startswith('subnet['):
                match = self.subnet_pattern.match(key)
                if match:
                    subnet_idx = int(match.group('subnet_idx')) - 1
                    key = match.group('metric')

                    if module is Module.DHCP4:
                        subnet = self.config['Dhcp4']['subnet4'][subnet_idx]
                    else:
                        subnet = self.config['Dhcp6']['subnet6'][subnet_idx]
                    labels['subnet'] = subnet['subnet']
                else:
                    click.echo('subnet pattern failed for metric: {0}'.format(
                        key), file=sys.stderr)

            if module is Module.DHCP4:
                metric_info = self.metrics_dhcp4_map[key]
                metric = self.metrics_dhcp4[metric_info['metric']]
            else:
                metric_info = self.metrics_dhcp6_map[key]
                metric = self.metrics_dhcp6[metric_info['metric']]

            # merge static and dynamic labels
            labels.update(metric_info.get('labels', {}))

            # export labels and value
            metric.labels(**labels).set(value)
