from __future__ import annotations

import logging

from prometheus_client.core import (
    GaugeMetricFamily,
)

from kea_exporter import DHCPVersion

logger = logging.getLogger(__name__)

BASE_LABELS = ["target", "server_tag"]

OPERATION_LABEL = ["operation"]

SUBNET_LABELS = ["subnet", "subnet_id"]

POOL_LABELS = ["pool"]


def labels_dict_to_list(metric, labels: dict) -> list:
    return_labels = []
    for label in metric._labelnames:
        return_labels.append(labels.get(label, ""))

    return return_labels


def get_server_metrics():
    return [
        GaugeMetricFamily("kea_dhcp4_packets_sent_total", "Packets sent", labels=[*BASE_LABELS, *OPERATION_LABEL]),
        GaugeMetricFamily(
            "kea_dhcp4_packets_received_total", "Packets received", labels=[*BASE_LABELS, *OPERATION_LABEL]
        ),
        GaugeMetricFamily("kea_dhcp6_packets_sent_total", "Packets sent", labels=[*BASE_LABELS, *OPERATION_LABEL]),
        GaugeMetricFamily(
            "kea_dhcp6_packets_received_total", "Packets received", labels=[*BASE_LABELS, *OPERATION_LABEL]
        ),
        GaugeMetricFamily(
            "kea_dhcp6_packets_sent_dhcp4_total",
            "DHCPv4-over-DHCPv6 Packets received",
            labels=[*BASE_LABELS, *OPERATION_LABEL],
        ),
        GaugeMetricFamily(
            "kea_dhcp6_packets_received_dhcp4_total",
            "DHCPv4-over-DHCPv6 Packets received",
            labels=[*BASE_LABELS, *OPERATION_LABEL],
        ),
    ]


def get_subnet_metrics():
    return [
        GaugeMetricFamily(
            "kea_dhcp4_allocations_failed_total", "Allocation fail count", labels=[*BASE_LABELS, *SUBNET_LABELS]
        ),
        GaugeMetricFamily(
            "kea_dhcp4_leases_reused_total",
            "Number of times an IPv4 lease has been renewed in memory",
            labels=[*BASE_LABELS, *SUBNET_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp4_addresses_assigned_total",
            "Assigned addresses",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp4_addresses_declined_total", "Declined counts", labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS]
        ),
        GaugeMetricFamily(
            "kea_dhcp4_addresses_declined_reclaimed_total",
            "Declined addresses that were reclaimed",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp4_addresses_reclaimed_total",
            "Expired addresses that were reclaimed",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp4_addresses_total",
            "Size of subnet address pool",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp4_reservation_conflicts_total", "Reservation conflict count", labels=[*BASE_LABELS, *SUBNET_LABELS]
        ),
        GaugeMetricFamily(
            "kea_dhcp6_allocations_failed_total", "Allocation fail count", labels=[*BASE_LABELS, *SUBNET_LABELS]
        ),
        GaugeMetricFamily(
            "kea_dhcp6_na_assigned_total",
            "Assigned non-temporary addresses (IA_NA)",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp6_pd_assigned_total", "Assigned prefix delegations (IA_PD)", labels=[*BASE_LABELS, *SUBNET_LABELS]
        ),
        GaugeMetricFamily(
            "kea_dhcp6_addresses_declined_total",
            "Declined addresses",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp6_addresses_declined_reclaimed_total",
            "Declined addresses that were reclaimed",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp6_addresses_reclaimed_total",
            "Expired addresses that were reclaimed",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp6_na_total",
            "Size of non-temporary address pool",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp6_pd_total", "Size of prefix delegation pool", labels=[*BASE_LABELS, *SUBNET_LABELS]
        ),
        GaugeMetricFamily(
            "kea_dhcp6_reservation_conflicts_total", "Reservation conflict count", labels=[*BASE_LABELS, *SUBNET_LABELS]
        ),
        GaugeMetricFamily(
            "kea_dhcp6_na_reuses_total",
            "Number of IA_NA lease reuses",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
        GaugeMetricFamily(
            "kea_dhcp6_pd_reuses_total",
            "Number of IA_PD lease reuses",
            labels=[*BASE_LABELS, *SUBNET_LABELS, *POOL_LABELS],
        ),
    ]


metric_map = {
    # IPv4
    "kea_dhcp4_packets_sent_total": [
        {"statistic": "pkt4-ack-sent", "labels": {"operation": "ack"}},
        {"statistic": "pkt4-nak-sent", "labels": {"operation": "nak"}},
        {"statistic": "pkt4-offer-sent", "labels": {"operation": "offer"}},
    ],
    "kea_dhcp4_packets_received_total": [
        {"statistic": "pkt4-discover-received", "labels": {"operation": "discover"}},
        {"statistic": "pkt4-offer-received", "labels": {"operation": "offer"}},
        {"statistic": "pkt4-request-received", "labels": {"operation": "request"}},
        {"statistic": "pkt4-ack-received", "labels": {"operation": "ack"}},
        {"statistic": "pkt4-nak-received", "labels": {"operation": "nak"}},
        {"statistic": "pkt4-release-received", "labels": {"operation": "release"}},
        {"statistic": "pkt4-decline-received", "labels": {"operation": "decline"}},
        {"statistic": "pkt4-inform-received", "labels": {"operation": "inform"}},
        {"statistic": "pkt4-unknown-received", "labels": {"operation": "unknown"}},
        {"statistic": "pkt4-parse-failed", "labels": {"operation": "parse-failed"}},
        {"statistic": "pkt4-receive-drop", "labels": {"operation": "drop"}},
    ],
    "kea_dhcp4_allocations_failed_total": [
        {"statistic": "v4-allocation-fail-subnet", "labels": {"context": "subnet"}},
        {"statistic": "v4-allocation-fail-shared-network", "labels": {"context": "shared-network"}},
        {"statistic": "v4-allocation-fail-no-pools", "labels": {"context": "no-pools"}},
        {"statistic": "v4-allocation-fail-classes", "labels": {"context": "classes"}},
    ],
    "kea_dhcp4_leases_reused_total": [{"statistic": "v4-lease-reuses", "labels": {}}],
    "kea_dhcp4_addresses_assigned_total": [{"statistic": "assigned-addresses", "labels": {}}],
    "kea_dhcp4_addresses_declined_total": [{"statistic": "declined-addresses", "labels": {}}],
    "kea_dhcp4_addresses_declined_reclaimed_total": [{"statistic": "reclaimed-declined-addresses", "labels": {}}],
    "kea_dhcp4_addresses_reclaimed_total": [{"statistic": "reclaimed-leases", "labels": {}}],
    "kea_dhcp4_addresses_total": [{"statistic": "total-addresses", "labels": {}}],
    "kea_dhcp4_reservation_conflicts_total": [{"statistic": "v4-reservation-conflicts", "labels": {}}],
    # IPv6
    "kea_dhcp6_packets_sent_total": [
        {"statistic": "pkt6-advertise-sent", "labels": {"operation": "advertise"}},
        {"statistic": "pkt6-reply-sent", "labels": {"operation": "reply"}},
    ],
    "kea_dhcp6_packets_received_total": [
        {"statistic": "pkt6-receive-drop", "labels": {"operation": "drop"}},
        {"statistic": "pkt6-parse-failed", "labels": {"operation": "parse-failed"}},
        {"statistic": "pkt6-solicit-received", "labels": {"operation": "solicit"}},
        {"statistic": "pkt6-advertise-received", "labels": {"operation": "advertise"}},
        {"statistic": "pkt6-request-received", "labels": {"operation": "request"}},
        {"statistic": "pkt6-reply-received", "labels": {"operation": "reply"}},
        {"statistic": "pkt6-renew-received", "labels": {"operation": "renew"}},
        {"statistic": "pkt6-rebind-received", "labels": {"operation": "rebind"}},
        {"statistic": "pkt6-release-received", "labels": {"operation": "release"}},
        {"statistic": "pkt6-decline-received", "labels": {"operation": "decline"}},
        {"statistic": "pkt6-infrequest-received", "labels": {"operation": "infrequest"}},
        {"statistic": "pkt6-unknown-received", "labels": {"operation": "unknown"}},
    ],
    "kea_dhcp6_packets_sent_dhcp4_total": [
        {"statistic": "pkt6-dhcpv4-response-sent", "labels": {"operation": "response"}}
    ],
    "kea_dhcp6_packets_received_dhcp4_total": [
        {"statistic": "pkt6-dhcpv4-query-received", "labels": {"operation": "query"}},
        {"statistic": "pkt6-dhcpv4-response-received", "labels": {"operation": "response"}},
    ],
    "kea_dhcp6_allocations_failed_total": [
        {"statistic": "v6-allocation-fail-shared-network", "labels": {"context": "shared-network"}},
        {"statistic": "v6-allocation-fail-subnet", "labels": {"context": "subnet"}},
        {"statistic": "v6-allocation-fail-no-pools", "labels": {"context": "no-pools"}},
        {"statistic": "v6-allocation-fail-classes", "labels": {"context": "classes"}},
    ],
    "kea_dhcp6_na_assigned_total": [{"statistic": "assigned-nas", "labels": {}}],
    "kea_dhcp6_pd_assigned_total": [{"statistic": "assigned-pds", "labels": {}}],
    "kea_dhcp6_addresses_declined_total": [{"statistic": "declined-addresses", "labels": {}}],
    "kea_dhcp6_addresses_declined_reclaimed_total": [
        {"statistic": "declined-reclaimed-addresses", "labels": {}},
        {"statistic": "reclaimed-declined-addresses", "labels": {}},
    ],
    "kea_dhcp6_addresses_reclaimed_total": [{"statistic": "reclaimed-leases", "labels": {}}],
    "kea_dhcp6_na_total": [{"statistic": "total-nas", "labels": {}}],
    "kea_dhcp6_pd_total": [{"statistic": "total-pds", "labels": {}}],
    "kea_dhcp6_reservation_conflicts_total": [{"statistic": "v6-reservation-conflicts", "labels": {}}],
    "kea_dhcp6_na_reuses_total": [{"statistic": "v6-ia-na-lease-reuses", "labels": {}}],
    "kea_dhcp6_pd_reuses_total": [{"statistic": "v6-ia-pd-lease-reuses", "labels": {}}],
}


class KeaMetrics:
    def __init__(self, all_stats):
        """
        :param all_stats: A dictionary where keys are labels and values are statistics for each source.
        """
        self.all_stats = all_stats

    def collect_metrics(self):
        """
        Create Prometheus metrics for all sources.
        """

        yield from self.collect_server_metrics()

        yield from self.collect_subnet_metrics()

    def collect_server_metrics(self):
        # Generate all server related metrics
        server_metrics = get_server_metrics()
        for server_metric in server_metrics:
            mapped_stats = metric_map.get(server_metric.name)

            for mapped_stat_dict in mapped_stats:
                mapped_stat = mapped_stat_dict.get("statistic", "")
                extra_labels = mapped_stat_dict.get("labels", {})

                for target, server_tag, dhcp_version, arguments, _ in self.all_stats:
                    if dhcp_version == DHCPVersion.DHCP4 and "dhcp4" not in server_metric.name:
                        # Looping DHCP4 but looking at data for dhcp6
                        continue
                    if dhcp_version == DHCPVersion.DHCP6 and "dhcp6" not in server_metric.name:
                        # Looping DHCP6 but looking at data for dhcp4
                        continue

                    try:
                        value = arguments.get(mapped_stat, [])[0][0]
                    except IndexError:
                        logging.debug(f"Did not find any value for metric: {server_metric.name}, stat: {mapped_stat}")
                        # Did not find any statistic regarding this pool, skipping
                        continue

                    base_labels = {"target": target, "server_tag": server_tag}
                    labels = labels_dict_to_list(server_metric, {**base_labels, **extra_labels})
                    server_metric.add_metric(value=value, labels=labels)
            yield server_metric

    def collect_subnet_metrics(self):
        # Generate all subnet related metrics
        subnet_metrics = get_subnet_metrics()

        for subnet_metric in subnet_metrics:
            mapped_stats = metric_map.get(subnet_metric.name)
            logger.debug(subnet_metric.name)
            for mapped_stat_dict in mapped_stats:
                mapped_stat = mapped_stat_dict.get("statistic", "")
                extra_labels = mapped_stat_dict.get("labels", {})

                logger.debug(f"Mapped_stat: {mapped_stat}")

                for target, server_tag, dhcp_version, arguments, subnets in self.all_stats:
                    if dhcp_version == DHCPVersion.DHCP4 and "dhcp4" not in subnet_metric.name:
                        # Looping DHCP4 but looking at data for dhcp6
                        continue
                    if dhcp_version == DHCPVersion.DHCP6 and "dhcp6" not in subnet_metric.name:
                        # Looping DHCP6 but looking at data for dhcp4
                        continue

                    base_labels = {"target": target, "server_tag": server_tag}
                    logging.debug(subnets)
                    for subnet in subnets:
                        subnet_id = subnet.get("id")

                        subnet_prefix = subnet.get("subnet")

                        logger.debug(f"Looping {subnet_prefix}")
                        try:
                            value = arguments.get(f"subnet[{subnet_id}].{mapped_stat}", [])[0][0]
                            logger.debug(f"Found value for {subnet_prefix} in {mapped_stat}")
                        except IndexError:
                            logger.debug(f"Did not find stat: {mapped_stat} for subnet: {subnet_prefix}")
                            # Did not find any statistic regarding this subnet, skipping
                            continue
                        subnet_labels = {"subnet": subnet_prefix, "subnet_id": str(subnet_id)}

                        labels = labels_dict_to_list(subnet_metric, {**base_labels, **subnet_labels, **extra_labels})
                        logger.debug(f"Adding {subnet_metric.name} for subnet: {subnet_prefix}")
                        subnet_metric.add_metric(value=value, labels=labels)
                        logger.debug(subnet_metric.samples)

                        # Add metrics for pools in the subnet
                        for pool_index, pool in enumerate(subnet.get("pools")):
                            # logger.debug(f"Looping pool: {pool_index}, {pool}")
                            try:
                                value = arguments.get(f"subnet[{subnet_id}].pool[{pool_index}].{mapped_stat}", [])[0][0]
                            except IndexError:
                                logger.debug(f"Did not find stat: {mapped_stat} for pool: {pool}")
                                continue
                            pool_labels = {
                                "subnet": subnet_prefix,
                                "subnet_id": str(subnet_id),
                                "pool": pool.get("pool"),
                            }

                            labels = labels_dict_to_list(subnet_metric, {**base_labels, **pool_labels, **extra_labels})
                            subnet_metric.add_metric(value=value, labels=labels)

            if subnet_metric.samples:
                logger.debug(f"yielding metric: {subnet_metric}")
                yield subnet_metric
            else:
                logger.debug(f"Skipping yielding metric: {subnet_metric}")
                pass
