import sys
import time

import click
from prometheus_client import REGISTRY, make_wsgi_app, start_http_server

from kea_exporter import __project__, __version__
from kea_exporter.exporter import Exporter


class Timer:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = time.time()

    def time_elapsed(self):
        now_time = time.time()
        return now_time - self.start_time


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
    "-i",
    "--interval",
    envvar="INTERVAL",
    type=int,
    default=0,
    help="Minimal interval between two queries to Kea in seconds.",
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
def cli(port, address, interval, **kwargs):
    exporter = Exporter(**kwargs)

    if not exporter.targets:
        sys.exit(1)

    httpd, _ = start_http_server(port, address)

    t = Timer()

    def local_wsgi_app(registry):
        func = make_wsgi_app(registry, False)

        def app(environ, start_response):
            if t.time_elapsed() >= interval:
                exporter.update()
                t.reset()
            output_array = func(environ, start_response)
            return output_array

        return app

    httpd.set_app(local_wsgi_app(REGISTRY))

    click.echo(f"Listening on http://{address}:{port}")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    cli()
