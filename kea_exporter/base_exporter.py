import re

from prometheus_client import Gauge


class BaseExporter:
    subnet_pattern = re.compile(
        r"^subnet\[(?P<subnet_id>[\d]+)\]\.(pool\[(?P<pool_index>[\d]+)\]\.(?P<pool_metric>[\w-]+)|(?P<subnet_metric>[\w-]+))$")

    def __init__(self):
        # prometheus
        self.prefix = 'kea'
        self.prefix_dhcp4 = f'{self.prefix}_dhcp4'
        self.prefix_dhcp6 = f'{self.prefix}_dhcp6'

        self.metrics_dhcp4 = None
        self.metrics_dhcp4_map = None
        self.metrics_dhcp4_global_ignore = None
        self.metrics_dhcp4_subnet_ignore = None
        self.setup_dhcp4_metrics()

        self.metrics_dhcp6 = None
        self.metrics_dhcp6_map = None
        self.metrics_dhcp6_global_ignore = None
        self.metrics_dhcp6_subnet_ignore = None
        self.setup_dhcp6_metrics()

        # track unhandled metric keys, to notify only once
        self.unhandled_metrics = set()


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

            # per Subnet or Subnet pool
            'addresses_allocation_fail': Gauge(
                f'{self.prefix_dhcp4}_allocations_failed_total',
                'Allocation fail count',
                ['subnet', 'subnet_id', 'context',]),
            'addresses_assigned_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_assigned_total',
                'Assigned addresses',
                ['subnet', 'subnet_id', 'pool']),
            'addresses_declined_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_declined_total',
                'Declined counts',
                ['subnet', 'subnet_id', 'pool']),
            'addresses_declined_reclaimed_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_declined_reclaimed_total',
                'Declined addresses that were reclaimed',
                ['subnet', 'subnet_id', 'pool']),
            'addresses_reclaimed_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_reclaimed_total',
                'Expired addresses that were reclaimed',
                ['subnet', 'subnet_id', 'pool']),
            'addresses_total': Gauge(
                f'{self.prefix_dhcp4}_addresses_total',
                'Size of subnet address pool',
                ['subnet', 'subnet_id', 'pool']),
            'reservation_conflicts_total': Gauge(
                f'{self.prefix_dhcp4}_reservation_conflicts_total',
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

            # per Subnet or pool
            'v4-allocation-fail-subnet' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'subnet'
                },
            },

            'v4-allocation-fail-shared-network' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'shared-network'
                },
            },

            'v4-allocation-fail-no-pools' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'no-pools'
                },
            },

            'v4-allocation-fail-classes' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'classes'
                },
            },
            'assigned-addresses': {
                'metric': 'addresses_assigned_total',
            },
            'declined-addresses': {
                'metric': 'addresses_declined_total',
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
                'metric' : 'reservation_conflicts_total',
            }
        }
        # Ignore list for Global level metrics
        self.metrics_dhcp4_global_ignore = [
            # metrics that exist at the subnet level in more detail
            'cumulative-assigned-addresses',
            'declined-addresses',
            # sums of different packet types
            'reclaimed-declined-addresses',
            'reclaimed-leases',
            'v4-reservation-conflicts',
            'v4-allocation-fail',
            'v4-allocation-fail-subnet',
            'v4-allocation-fail-shared-network',
            'v4-allocation-fail-no-pools',
            'v4-allocation-fail-classes',
            'pkt4-sent',
            'pkt4-received',

        ]
        # Ignore list for subnet level metrics
        self.metric_dhcp4_subnet_ignore = [
            'cumulative-assigned-addresses',
            'v4-allocation-fail',
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

            # per Subnet or pool
            'addresses_allocation_fail': Gauge(
                f'{self.prefix_dhcp6}_allocations_failed_total',
                'Allocation fail count',
                ['subnet', 'subnet_id', 'context',]),
            'addresses_declined_total': Gauge(
                f'{self.prefix_dhcp6}_addresses_declined_total',
                'Declined addresses',
                ['subnet', 'subnet_id', 'pool']),
            'addresses_declined_reclaimed_total': Gauge(
                f'{self.prefix_dhcp6}_addresses_declined_reclaimed_total',
                'Declined addresses that were reclaimed',
                ['subnet', 'subnet_id', 'pool']),
            'addresses_reclaimed_total': Gauge(
                f'{self.prefix_dhcp6}_addresses_reclaimed_total',
                'Expired addresses that were reclaimed',
                ['subnet', 'subnet_id', 'pool']),
            'reservation_conflicts_total': Gauge(
                f'{self.prefix_dhcp6}_reservation_conflicts_total',
                'Reservation conflict count',
                ['subnet', 'subnet_id']),

            # IA_NA
            'na_assigned_total': Gauge(
                f'{self.prefix_dhcp6}_na_assigned_total',
                'Assigned non-temporary addresses (IA_NA)',
                ['subnet', 'subnet_id', 'pool']),
            'na_total': Gauge(
                f'{self.prefix_dhcp6}_na_total',
                'Size of non-temporary address pool',
                ['subnet', 'subnet_id', 'pool']
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
            'v6-allocation-fail-shared-network' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'shared-network'
                },
            },

            'v6-allocation-fail-subnet' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'subnet'
                },
            },

            'v6-allocation-fail-no-pools' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'no-pools'
                },
            },

            'v6-allocation-fail-classes' :{
                'metric' : 'addresses_allocation_fail',
                'labels': {
                    'context': 'classes'
                },
            },
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
                'metric' : 'reservation_conflicts_total',
            },
        }

        # Ignore list for Global level metrics
        self.metrics_dhcp6_global_ignore = [
            # metrics that exist at the subnet level in more detail
            'cumulative-assigned-addresses',
            'declined-addresses',
            # sums of different packet types
            'cumulative-assigned-nas',
            'cumulative-assigned-pds',
            'reclaimed-declined-addresses',
            'reclaimed-leases',
            'v6-reservation-conflicts',
            'v6-allocation-fail',
            'v6-allocation-fail-subnet',
            'v6-allocation-fail-shared-network',
            'v6-allocation-fail-no-pools',
            'v6-allocation-fail-classes',
            'pkt6-sent',
            'pkt6-received',

        ]
        # Ignore list for subnet level metrics
        self.metric_dhcp6_subnet_ignore = [
            'cumulative-assigned-addresses',
            'cumulative-assigned-nas',
            'cumulative-assigned-pds',
            'v6-allocation-fail',
        ]
