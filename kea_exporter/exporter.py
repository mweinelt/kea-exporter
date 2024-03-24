import re
import sys
from urllib.parse import urlparse

import click
from prometheus_client import Gauge, Counter, disable_created_metrics

from kea_exporter import DHCPVersion
from kea_exporter.http import KeaHTTPClient
from kea_exporter.uds import KeaSocketClient


disable_created_metrics()


class Exporter:
    subnet_pattern = re.compile(
        r"^subnet\[(?P<subnet_id>[\d]+)\]\.(pool\[(?P<pool_index>[\d]+)\]\.(?P<pool_metric>[\w-]+)|(?P<subnet_metric>[\w-]+))$"
    )

    def __init__(self, targets, **kwargs):
        # prometheus
        self.prefix = "kea"
        self.prefix_dhcp4 = f"{self.prefix}_dhcp4"
        self.prefix_dhcp6 = f"{self.prefix}_dhcp6"

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

        # track missing info, to notify only once
        self.subnet_missing_info_sent = {
            DHCPVersion.DHCP4: [],
            DHCPVersion.DHCP6: [],
        }

        self.targets = []
        for target in targets:
            url = urlparse(target)
            client = None
            try:
                if url.scheme:
                    client = KeaHTTPClient(target, **kwargs)
                elif url.path:
                    client = KeaSocketClient(target, **kwargs)
                else:
                    click.echo(f"Unable to parse target argument: {target}")
                    continue
            except OSError as ex:
                click.echo(ex)
                continue

            self.targets.append(client)

    def update(self):
        for target in self.targets:
            for response in target.stats():
                self.parse_metrics(*response)

    def setup_dhcp4_metrics(self):
        self.metrics_dhcp4 = {
            # Packets
            "sent_packets": Counter(f"{self.prefix_dhcp4}_packets_sent_total", "Packets sent", ["operation"]),
            "received_packets": Counter(
                f"{self.prefix_dhcp4}_packets_received_total",
                "Packets received",
                ["operation"],
            ),
            # per Subnet or Subnet pool
            "addresses_allocation_fail": Counter(
                f"{self.prefix_dhcp4}_allocations_failed_total",
                "Allocation fail count",
                [
                    "subnet",
                    "subnet_id",
                    "context",
                ],
            ),
            "addresses_assigned_total": Gauge(
                f"{self.prefix_dhcp4}_addresses_assigned_total",
                "Assigned addresses",
                ["subnet", "subnet_id", "pool"],
            ),
            "addresses_declined_total": Gauge(
                f"{self.prefix_dhcp4}_addresses_declined_total",
                "Declined counts",
                ["subnet", "subnet_id", "pool"],
            ),
            "addresses_declined_reclaimed_total": Counter(
                f"{self.prefix_dhcp4}_addresses_declined_reclaimed_total",
                "Declined addresses that were reclaimed",
                ["subnet", "subnet_id", "pool"],
            ),
            "addresses_reclaimed_total": Counter(
                f"{self.prefix_dhcp4}_addresses_reclaimed_total",
                "Expired addresses that were reclaimed",
                ["subnet", "subnet_id", "pool"],
            ),
            "addresses_total": Gauge(
                f"{self.prefix_dhcp4}_addresses_total",
                "Size of subnet address pool",
                ["subnet", "subnet_id", "pool"],
            ),
            "reservation_conflicts_total": Counter(
                f"{self.prefix_dhcp4}_reservation_conflicts_total",
                "Reservation conflict count",
                ["subnet", "subnet_id"],
            ),
            "leases_reused_total": Gauge(
                f"{self.prefix_dhcp4}_leases_reused_total",
                "Number of times an IPv4 lease has been renewed in memory",
                ["subnet", "subnet_id"],
            ),
        }

        self.metrics_dhcp4_map = {
            # sent_packets
            "pkt4-ack-sent": {
                "metric": "sent_packets",
                "labels": {"operation": "ack"},
            },
            "pkt4-nak-sent": {
                "metric": "sent_packets",
                "labels": {"operation": "nak"},
            },
            "pkt4-offer-sent": {
                "metric": "sent_packets",
                "labels": {"operation": "offer"},
            },
            # received_packets
            "pkt4-discover-received": {
                "metric": "received_packets",
                "labels": {"operation": "discover"},
            },
            "pkt4-offer-received": {
                "metric": "received_packets",
                "labels": {"operation": "offer"},
            },
            "pkt4-request-received": {
                "metric": "received_packets",
                "labels": {"operation": "request"},
            },
            "pkt4-ack-received": {
                "metric": "received_packets",
                "labels": {"operation": "ack"},
            },
            "pkt4-nak-received": {
                "metric": "received_packets",
                "labels": {"operation": "nak"},
            },
            "pkt4-release-received": {
                "metric": "received_packets",
                "labels": {"operation": "release"},
            },
            "pkt4-decline-received": {
                "metric": "received_packets",
                "labels": {"operation": "decline"},
            },
            "pkt4-inform-received": {
                "metric": "received_packets",
                "labels": {"operation": "inform"},
            },
            "pkt4-unknown-received": {
                "metric": "received_packets",
                "labels": {"operation": "unknown"},
            },
            "pkt4-parse-failed": {
                "metric": "received_packets",
                "labels": {"operation": "parse-failed"},
            },
            "pkt4-receive-drop": {
                "metric": "received_packets",
                "labels": {"operation": "drop"},
            },
            # per Subnet or pool
            "v4-allocation-fail-subnet": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "subnet"},
            },
            "v4-allocation-fail-shared-network": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "shared-network"},
            },
            "v4-allocation-fail-no-pools": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "no-pools"},
            },
            "v4-allocation-fail-classes": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "classes"},
            },
            "v4-lease-reuses": {
                "metric": "leases_reused_total",
            },
            "assigned-addresses": {
                "metric": "addresses_assigned_total",
            },
            "declined-addresses": {
                "metric": "addresses_declined_total",
            },
            "reclaimed-declined-addresses": {
                "metric": "addresses_declined_reclaimed_total",
            },
            "reclaimed-leases": {
                "metric": "addresses_reclaimed_total",
            },
            "total-addresses": {
                "metric": "addresses_total",
            },
            "v4-reservation-conflicts": {
                "metric": "reservation_conflicts_total",
            },
        }
        # Ignore list for Global level metrics
        self.metrics_dhcp4_global_ignore = [
            # metrics that exist at the subnet level in more detail
            "cumulative-assigned-addresses",
            "declined-addresses",
            # sums of different packet types
            "reclaimed-declined-addresses",
            "reclaimed-leases",
            "v4-reservation-conflicts",
            "v4-allocation-fail",
            "v4-allocation-fail-subnet",
            "v4-allocation-fail-shared-network",
            "v4-allocation-fail-no-pools",
            "v4-allocation-fail-classes",
            "pkt4-sent",
            "pkt4-received",
            "v4-lease-reuses",
        ]
        # Ignore list for subnet level metrics
        self.metric_dhcp4_subnet_ignore = [
            "cumulative-assigned-addresses",
            "v4-allocation-fail",
        ]

    def setup_dhcp6_metrics(self):
        self.metrics_dhcp6 = {
            # Packets sent/received
            "sent_packets": Counter(f"{self.prefix_dhcp6}_packets_sent_total", "Packets sent", ["operation"]),
            "received_packets": Counter(
                f"{self.prefix_dhcp6}_packets_received_total",
                "Packets received",
                ["operation"],
            ),
            # DHCPv4-over-DHCPv6
            "sent_dhcp4_packets": Counter(
                f"{self.prefix_dhcp6}_packets_sent_dhcp4_total",
                "DHCPv4-over-DHCPv6 Packets sent",
                ["operation"],
            ),
            "received_dhcp4_packets": Counter(
                f"{self.prefix_dhcp6}_packets_received_dhcp4_total",
                "DHCPv4-over-DHCPv6 Packets received",
                ["operation"],
            ),
            # per Subnet or pool
            "addresses_allocation_fail": Counter(
                f"{self.prefix_dhcp6}_allocations_failed_total",
                "Allocation fail count",
                [
                    "subnet",
                    "subnet_id",
                    "context",
                ],
            ),
            "addresses_declined_total": Gauge(
                f"{self.prefix_dhcp6}_addresses_declined_total",
                "Declined addresses",
                ["subnet", "subnet_id", "pool"],
            ),
            "addresses_declined_reclaimed_total": Counter(
                f"{self.prefix_dhcp6}_addresses_declined_reclaimed_total",
                "Declined addresses that were reclaimed",
                ["subnet", "subnet_id", "pool"],
            ),
            "addresses_reclaimed_total": Counter(
                f"{self.prefix_dhcp6}_addresses_reclaimed_total",
                "Expired addresses that were reclaimed",
                ["subnet", "subnet_id", "pool"],
            ),
            "reservation_conflicts_total": Counter(
                f"{self.prefix_dhcp6}_reservation_conflicts_total",
                "Reservation conflict count",
                ["subnet", "subnet_id"],
            ),
            # IA_NA
            "na_assigned_total": Gauge(
                f"{self.prefix_dhcp6}_na_assigned_total",
                "Assigned non-temporary addresses (IA_NA)",
                ["subnet", "subnet_id", "pool"],
            ),
            "na_total": Gauge(
                f"{self.prefix_dhcp6}_na_total",
                "Size of non-temporary address pool",
                ["subnet", "subnet_id", "pool"],
            ),
            "na_reuses_total": Gauge(
                f"{self.prefix_dhcp6}_na_reuses_total", "Number of IA_NA lease reuses", ["subnet", "subnet_id", "pool"]
            ),
            # IA_PD
            "pd_assigned_total": Gauge(
                f"{self.prefix_dhcp6}_pd_assigned_total",
                "Assigned prefix delegations (IA_PD)",
                ["subnet", "subnet_id"],
            ),
            "pd_total": Gauge(
                f"{self.prefix_dhcp6}_pd_total",
                "Size of prefix delegation pool",
                ["subnet", "subnet_id"],
            ),
            "pd_reuses_total": Gauge(
                f"{self.prefix_dhcp6}_pd_reuses_total", "Number of IA_PD lease reuses", ["subnet", "subnet_id", "pool"]
            ),
        }

        self.metrics_dhcp6_map = {
            # sent_packets
            "pkt6-advertise-sent": {
                "metric": "sent_packets",
                "labels": {"operation": "advertise"},
            },
            "pkt6-reply-sent": {
                "metric": "sent_packets",
                "labels": {"operation": "reply"},
            },
            # received_packets
            "pkt6-receive-drop": {
                "metric": "received_packets",
                "labels": {"operation": "drop"},
            },
            "pkt6-parse-failed": {
                "metric": "received_packets",
                "labels": {"operation": "parse-failed"},
            },
            "pkt6-solicit-received": {
                "metric": "received_packets",
                "labels": {"operation": "solicit"},
            },
            "pkt6-advertise-received": {
                "metric": "received_packets",
                "labels": {"operation": "advertise"},
            },
            "pkt6-request-received": {
                "metric": "received_packets",
                "labels": {"operation": "request"},
            },
            "pkt6-reply-received": {
                "metric": "received_packets",
                "labels": {"operation": "reply"},
            },
            "pkt6-renew-received": {
                "metric": "received_packets",
                "labels": {"operation": "renew"},
            },
            "pkt6-rebind-received": {
                "metric": "received_packets",
                "labels": {"operation": "rebind"},
            },
            "pkt6-release-received": {
                "metric": "received_packets",
                "labels": {"operation": "release"},
            },
            "pkt6-decline-received": {
                "metric": "received_packets",
                "labels": {"operation": "decline"},
            },
            "pkt6-infrequest-received": {
                "metric": "received_packets",
                "labels": {"operation": "infrequest"},
            },
            "pkt6-unknown-received": {
                "metric": "received_packets",
                "labels": {"operation": "unknown"},
            },
            # DHCPv4-over-DHCPv6
            "pkt6-dhcpv4-response-sent": {
                "metric": "sent_dhcp4_packets",
                "labels": {"operation": "response"},
            },
            "pkt6-dhcpv4-query-received": {
                "metric": "received_dhcp4_packets",
                "labels": {"operation": "query"},
            },
            "pkt6-dhcpv4-response-received": {
                "metric": "received_dhcp4_packets",
                "labels": {"operation": "response"},
            },
            # per Subnet
            "v6-allocation-fail-shared-network": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "shared-network"},
            },
            "v6-allocation-fail-subnet": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "subnet"},
            },
            "v6-allocation-fail-no-pools": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "no-pools"},
            },
            "v6-allocation-fail-classes": {
                "metric": "addresses_allocation_fail",
                "labels": {"context": "classes"},
            },
            "assigned-nas": {
                "metric": "na_assigned_total",
            },
            "assigned-pds": {
                "metric": "pd_assigned_total",
            },
            "declined-addresses": {
                "metric": "addresses_declined_total",
            },
            "declined-reclaimed-addresses": {
                "metric": "addresses_declined_reclaimed_total",
            },
            "reclaimed-declined-addresses": {
                "metric": "addresses_declined_reclaimed_total",
            },
            "reclaimed-leases": {
                "metric": "addresses_reclaimed_total",
            },
            "total-nas": {
                "metric": "na_total",
            },
            "total-pds": {
                "metric": "pd_total",
            },
            "v6-reservation-conflicts": {
                "metric": "reservation_conflicts_total",
            },
            "v6-ia-na-lease-reuses": {"metric": "na_reuses_total"},
            "v6-ia-pd-lease-reuses": {"metric": "pd_reuses_total"},
        }

        # Ignore list for Global level metrics
        self.metrics_dhcp6_global_ignore = [
            # metrics that exist at the subnet level in more detail
            "cumulative-assigned-addresses",
            "declined-addresses",
            # sums of different packet types
            "cumulative-assigned-nas",
            "cumulative-assigned-pds",
            "reclaimed-declined-addresses",
            "reclaimed-leases",
            "v6-reservation-conflicts",
            "v6-allocation-fail",
            "v6-allocation-fail-subnet",
            "v6-allocation-fail-shared-network",
            "v6-allocation-fail-no-pools",
            "v6-allocation-fail-classes",
            "v6-ia-na-lease-reuses",
            "v6-ia-pd-lease-reuses",
            "pkt6-sent",
            "pkt6-received",
        ]
        # Ignore list for subnet level metrics
        self.metric_dhcp6_subnet_ignore = [
            "cumulative-assigned-addresses",
            "cumulative-assigned-nas",
            "cumulative-assigned-pds",
            "v6-allocation-fail",
        ]

    def parse_metrics(self, dhcp_version, arguments, subnets):
        for key, data in arguments.items():
            if dhcp_version is DHCPVersion.DHCP4:
                if key in self.metrics_dhcp4_global_ignore:
                    continue
            elif dhcp_version is DHCPVersion.DHCP6:
                if key in self.metrics_dhcp6_global_ignore:
                    continue
            else:
                continue

            value, _ = data[0]
            labels = {}

            subnet_match = self.subnet_pattern.match(key)
            if subnet_match:
                subnet_id = int(subnet_match.group("subnet_id"))
                pool_index = subnet_match.group("pool_index")
                pool_metric = subnet_match.group("pool_metric")
                subnet_metric = subnet_match.group("subnet_metric")

                if dhcp_version is DHCPVersion.DHCP4:
                    if (
                        pool_metric in self.metric_dhcp4_subnet_ignore
                        or subnet_metric in self.metric_dhcp4_subnet_ignore
                    ):
                        continue
                elif dhcp_version is DHCPVersion.DHCP6:
                    if (
                        pool_metric in self.metric_dhcp6_subnet_ignore
                        or subnet_metric in self.metric_dhcp6_subnet_ignore
                    ):
                        continue
                else:
                    continue

                subnet_data = subnets.get(subnet_id, [])
                if not subnet_data:
                    if subnet_id not in self.subnet_missing_info_sent.get(dhcp_version, []):
                        self.subnet_missing_info_sent.get(dhcp_version, []).append(subnet_id)
                        click.echo(
                            "Ignoring metric because subnet vanished from configuration: "
                            f"{dhcp_version.name=}, {subnet_id=}",
                            file=sys.stderr,
                        )
                    continue

                labels["subnet"] = subnet_data.get("subnet")
                labels["subnet_id"] = subnet_id

                # Check if subnet matches the pool_index
                if pool_index:
                    # Matched for subnet pool metrics
                    pool_index = int(pool_index)
                    subnet_pools = [pool.get("pool") for pool in subnet_data.get("pools", [])]

                    if len(subnet_pools) <= pool_index:
                        if f"{subnet_id}-{pool_index}" not in self.subnet_missing_info_sent.get(dhcp_version, []):
                            self.subnet_missing_info_sent.get(dhcp_version, []).append(f"{subnet_id}-{pool_index}")
                            click.echo(
                                "Ignoring metric because subnet vanished from configuration: "
                                f"{dhcp_version.name=}, {subnet_id=}, {pool_index=}",
                                file=sys.stderr,
                            )
                        continue
                    key = pool_metric
                    labels["pool"] = subnet_pools[pool_index]
                else:
                    # Matched for subnet metrics
                    key = subnet_metric
                    labels["pool"] = ""

            if dhcp_version is DHCPVersion.DHCP4:
                metrics_map = self.metrics_dhcp4_map
                metrics = self.metrics_dhcp4
            elif dhcp_version is DHCPVersion.DHCP6:
                metrics_map = self.metrics_dhcp6_map
                metrics = self.metrics_dhcp6
            else:
                continue

            try:
                metric_info = metrics_map[key]
            except KeyError:
                if key not in self.unhandled_metrics:
                    click.echo(
                        f"Unhandled metric '{key}' please file an issue at https://github.com/mweinelt/kea-exporter"
                    )
                    self.unhandled_metrics.add(key)
                continue

            metric = metrics[metric_info["metric"]]

            # merge static and dynamic labels
            labels.update(metric_info.get("labels", {}))

            # Filter labels that are not configured for the metric
            labels = {key: val for key, val in labels.items() if key in metric._labelnames}

            # export labels and value
            if isinstance(metric, Gauge):
                metric.labels(**labels).set(value)
            else:
                current_value = metric.labels(**labels)._value.get()

                # Attempt to handle counter resets (may not catch all cases)
                # e.g resetting the metric with kea command, let the metric grow to its previous value, query the statistics
                if value < current_value:
                    current_value = 0
                    metric.labels(**labels).reset()

                if value > current_value:
                    metric.labels(**labels).inc(value - current_value)
