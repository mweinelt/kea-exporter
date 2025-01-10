from collections.abc import Iterator

from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
from prometheus_client.registry import Collector

from kea_exporter.exporter import KeaExporter
from kea_exporter.metrics import KeaMetrics


class KeaCollector(Collector):
    def __init__(self, exporter: KeaExporter) -> None:
        super().__init__()
        self.exporter = exporter

    def collect(self) -> Iterator[GaugeMetricFamily]:
        # Get all stats from the exporter.
        all_stats = self.exporter.get_all_stats()

        kea_metrics = KeaMetrics(list(all_stats))

        yield from kea_metrics.collect_metrics()
