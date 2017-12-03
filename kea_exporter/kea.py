import re
import socket
import sys


import click
import hjson as json
import inotify.adapters
import inotify.constants
from prometheus_client import Gauge


class KeaExporter:
    subnet_pattern = re.compile(
        r"subnet\[(?P<subnet_idx>[\d]+)\]\.(?P<metric>[\w-]+)")

    def __init__(self, config_path='/etc/kea/kea-dhcp4.conf'):
        # kea control socket
        self.sock_dhcp6 = None
        self.sock_dhcp6_path = None
        self.sock_dhcp4 = None
        self.sock_dhcp4_path = None

        self.msg_statistics_all = bytes(
            json.dumpsJSON({'command': 'statistic-get-all'}), 'utf-8')

        # prometheus
        self.prefix = 'kea'
        self.prefix_dhcp4 = '{0}_dhcp4'.format(self.prefix)
        self.prefix_dhcp6 = '{0}_dhcp6'.format(self.prefix)

        self.metrics_dhcp4 = None
        self.metrics_dhcp4_map = None
        self.metrics_dhcp4_ignore = None
        self.setup_dhcp4_metrics()
        self.setup_dhcp6_metrics()

        self.metrics_dhcp6 = None
        self.metrics_dhcp6_map = None
        self.metrics_dhcp6_ignore = None

        # kea config
        self.config_path = config_path
        self.config = None

        self.inotify = inotify.adapters.Inotify()
        self.inotify.add_watch(
            bytes(config_path, 'utf-8'), mask=inotify.constants.IN_MODIFY
        )

        self.load_config()

    def load_config(self):
        with open(self.config_path, 'r') as handle:
            self.config = json.load(handle)

        try:
            sock4_path = self.config['Dhcp4']['control-socket']['socket-name']
            self.sock_dhcp4 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock_dhcp4.connect(sock4_path)
            click.echo('connected to Dhcp4 control socket at {}.'.format(
                sock4_path))
        except KeyError:
            click.echo('Dhcp4.control-socket.socket-name not configured, '
                       'will not be exporting Dhcp4 metrics', file=sys.stderr)
        except FileNotFoundError:
            click.echo('Dhcp4 control socket configured, but it does not exist.'
                       ' Is Kea running?', file=sys.stderr)

        try:
            sock6_path = self.config['Dhcp6']['control-socket']['socket-name']
            self.sock_dhcp6 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock_dhcp6.connect(sock6_path)
            click.echo('connected to Dhcp6 control socket at {}.'.format(
                sock6_path))
        except KeyError:
            click.echo('Dhcp6.control-socket.socket-name not configured, '
                       'will not be exporting Dhcp6 metrics', file=sys.stderr)
        except FileNotFoundError:
            click.echo('Dhcp6 control socket configured, but it does not exist.'
                       ' Is Kea running?', file=sys.stderr)

    def setup_dhcp4_metrics(self):
        self.metrics_dhcp4 = {
            'sent_packets': Gauge(
                '{0}_packets_sent_total'.format(self.prefix_dhcp4),
                'Packets sent',
                ['operation']),
            'received_packets': Gauge(
                '{0}_packets_received_total'.format(self.prefix_dhcp4),
                'Packets received',
                ['operation']),
            'addresses_assigned_total': Gauge(
                '{0}_addresses_assigned_total'.format(self.prefix_dhcp4),
                'Assigned addresses',
                ['subnet']),
            'addresses_declined_total': Gauge(
                '{0}_addresses_declined_total'.format(self.prefix_dhcp4),
                'Declined  counts',
                ['subnet']),
            'addresses_declined_reclaimed_total': Gauge(
                '{0}_addresses_declined_reclaimed_total'.format(self.prefix_dhcp4),
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
            'pkt4-request-received': {
                'metric': 'received_packets',
                'labels': {
                    'operation': 'request'
                }
            },

            # leases_total
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
            'reclaimed-leases'
        ]

    def parse_dhcp4_metrics(self, response):
        args = response['arguments']

        for key, data in args.items():
            if key in self.metrics_dhcp4_ignore:
                continue

            value, timestamp = data[0]
            labels = {}

            # lookup subnet
            if key.startswith('subnet['):
                match = self.subnet_pattern.match(key)
                if match:
                    subnet_idx = int(match.group('subnet_idx')) - 1
                    key = match.group('metric')

                    subnet = self.config['Dhcp4']['subnet4'][subnet_idx]
                    labels['subnet'] = subnet['subnet']
                else:
                    click.echo('subnet pattern failed for metric: {0}'.format(
                        key), file=sys.stderr)

            metric_info = self.metrics_dhcp4_map[key]

            # merge static and dynamic labels
            labels.update(metric_info.get('labels', {}))

            metric = self.metrics_dhcp4[metric_info['metric']]
            metric.labels(**labels).set(value)

    def setup_dhcp6_metrics(self):
        # TODO: implement me
        pass

    def parse_dhcp6_metrics(self, response):
        # TODO: implement me
        pass

    def update(self):
        reload_config = False
        for event in self.inotify.event_gen():
            if not event:
                break
            reload_config = True

        if reload_config:
            click.echo('Config was modified, reloading...', file=sys.stderr)
            self.load_config()

        if self.sock_dhcp4:
            self.sock_dhcp4.send(self.msg_statistics_all)
            response = self.sock_dhcp4.recv(4096).decode()
            self.parse_dhcp4_metrics(json.loads(response))

        if self.sock_dhcp6:
            self.sock_dhcp6.send(self.msg_statistics_all)
            response = self.sock_dhcp6.recv(4096).decode()
            self.parse_dhcp6_metrics(json.loads(response))
