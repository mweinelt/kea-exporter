import time

import click
from prometheus_client import start_http_server

from . import __project__, __version__


@click.command()
@click.option(
    "-m",
    "--mode",
    envvar="MODE",
    default="socket",
    help="Select mode.",
    type=click.Choice(["socket", "http"], case_sensitive=True),
)
@click.option(
    "-a",
    "--address",
    envvar="ADDRESS",
    default="0.0.0.0",
    help="Specify the address to bind against.",
)
@click.option(
    "-p",
    "--port",
    envvar="PORT",
    type=int,
    default=9547,
    help="Specify the port on which to listen.",
)
@click.option(
    "-i",
    "--interval",
    envvar="INTERVAL",
    type=int,
    default=7.5,
    help="Specify the metrics update interval in seconds.",
)
@click.option(
    "-t",
    "--target",
    envvar="TARGET",
    type=str,
    help="Target address and port of Kea server, e.g. http://kea.example.com:8080.",
)
@click.option(
    "--client-cert",
    envvar="CLIENT_CERT",
    type=str,
    help="Client certificate file path used in HTTP mode with mTLS",
    required=False,
)
@click.option(
    "--client-key",
    envvar="CLIENT_KEY",
    type=str,
    help="Client key file path used in HTTP mode with mTLS",
    required=False,
)
@click.argument("sockets", envvar="SOCKETS", nargs=-1, required=False)
@click.version_option(prog_name=__project__, version=__version__)
def cli(mode, port, address, interval, **kwargs):
    if mode == "socket":
        from .kea_socket_exporter import KeaSocketExporter as KeaExporter
    elif mode == "http":
        from .kea_http_exporter import KeaHTTPExporter as KeaExporter

    exporter = KeaExporter(**kwargs)
    exporter.update()

    start_http_server(port, address)
    click.echo(f"Listening on http://{address}:{port}")

    while True:
        time.sleep(interval)
        exporter.update()


if __name__ == "__main__":
    cli()
