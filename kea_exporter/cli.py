import time

import click
from prometheus_client import start_http_server

from . import __PROJECT__, __VERSION__
from .kea import KeaExporter, KeaSocket


@click.command()
@click.argument('sockets', nargs=-1, required=True)
@click.option('--address', default='0.0.0.0', help='Specify the address to bind against.')
@click.option('--port', type=int, default=9547, help='Specify the port on which to listen.')
@click.option('--interval', type=int, default=7.5, help='Specify the metrics update interval in seconds.')
@click.version_option(prog_name=__PROJECT__, version=__VERSION__)
def cli(sockets, address, port, interval):
    start_http_server(port, address)
    click.echo("Listening on http://{0}:{1}".format(address, port))

    sockets = [KeaSocket(socket) for socket in sockets]
    exporter = KeaExporter(sockets)
    exporter.update()

    while True:
        time.sleep(interval)
        exporter.update()


if __name__ == '__main__':
    cli()
