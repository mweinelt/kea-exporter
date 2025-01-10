import logging
from urllib.parse import urlparse

from kea_exporter.http import KeaHTTPClient
from kea_exporter.uds import KeaSocketClient

logger = logging.getLogger(__name__)


class KeaExporter:
    def __init__(self, targets, **kwargs):
        # prometheus

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
                    logger.warning(f"Unable to parse target argument: {target}")
                    continue
            except OSError as ex:
                logger.error(ex)
                continue

            self.targets.append(client)

    def get_all_stats(self):
        for target in self.targets:
            yield from target.stats()
