import time

import click
from prometheus_client import REGISTRY, make_wsgi_app, start_http_server

from . import __project__, __version__


class Timer():
    def __init__(self):
        self.reset()
    def reset(self):
        self.start_time = time.time()
    def time_elapsed(self):
        now_time = time.time()
        return now_time - self.start_time

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
    default=0,
    help="Minimal interval between two queries to Kea in seconds.",
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
