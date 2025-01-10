import logging
import sys
import time

import click
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY

from kea_exporter import __project__, __version__
from kea_exporter.collector import KeaCollector
from kea_exporter.exporter import KeaExporter

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-a",
    "--address",
    envvar="ADDRESS",
    type=str,
    default="0.0.0.0",
    help="Address that the exporter binds to.",
)
@click.option(
    "-p",
    "--port",
    envvar="PORT",
    type=int,
    default=9547,
    help="Port that the exporter binds to.",
)
@click.option(
    "-d",
    "--debug",
    envvar="DEBUG",
    type=bool,
    default=False,
    is_flag=True,
    help="Run kea_exporter in debug mode.",
)
@click.option(
    "--client-cert",
    envvar="CLIENT_CERT",
    type=click.Path(exists=True),
    help="Path to client certificate used to in HTTP requests",
    required=False,
)
@click.option(
    "--client-key",
    envvar="CLIENT_KEY",
    type=click.Path(exists=True),
    help="Path to client key used in HTTP requests",
    required=False,
)
@click.argument("targets", envvar="TARGETS", nargs=-1, required=True)
@click.version_option(prog_name=__project__, version=__version__)
def cli(port, address, debug, **kwargs):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    exporter = KeaExporter(**kwargs)

    start_http_server(port, address)

    if not exporter.targets:
        sys.exit(1)

    collector = KeaCollector(exporter)

    REGISTRY.register(collector)

    logger.info(f"Listening on http://{address}:{port}")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    cli()
