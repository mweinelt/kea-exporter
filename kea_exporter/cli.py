import time
import click

from prometheus_client import start_http_server

from . import __PROJECT__, __VERSION__

@click.command()
@click.option('-m', '--mode', envvar='MODE', default='socket', type=click.Choice(['socket', 'http'], case_sensitive=True))
@click.option('-a', '--address', envvar='ADDRESS', default='0.0.0.0', help='Specify the address to bind against.')
@click.option('-p', '--port', envvar='PORT', type=int, default=9547, help='Specify the port on which to listen.')
@click.option('-i', '--interval', envvar='INTERVAL', type=int, default=7.5, help='Specify the metrics update interval in seconds.')
@click.option('-t', '--target', envvar='TARGET', type=str, help='Target address and port of Kea server, e.g. http://kea.example.com:8080.')
@click.argument('sockets', envvar='SOCKETS', nargs=-1, required=False)
@click.version_option(prog_name=__PROJECT__, version=__VERSION__)
def cli(mode, port, address, interval, **kwargs):
    
    if mode == "socket":
        from .kea_socket_exporter import KeaSocketExporter as KeaExporter
    elif mode == "http":
        from .kea_http_exporter import KeaHTTPExporter as KeaExporter

    exporter = KeaExporter(**kwargs)
    exporter.update()
    
    start_http_server(port, address)
    click.echo("Listening on http://{0}:{1}".format(address, port))

    while True:
        time.sleep(interval)
        exporter.update()


if __name__ == '__main__':
    cli()
