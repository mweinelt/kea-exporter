kea-exporter
============

Prometheus Exporter for the ISC Kea DHCP Server.


Installation
------------

The latest stable version can be installed from PyPi:

::

    $ pip install kea-exporter


Features
--------

- DHCP4 Metrics (tested against Kea 1.1.0 only for now)
- Querying via control sockets
- Automatic config reload (through inotify)


Usage
-----

::

    Usage: kea-exporter [OPTIONS] CONFIG COMMAND [ARGS]...

    Options:
      --address TEXT      Specify the address to bind against.
      --port INTEGER      Specify the port on which to listen.
      --interval INTEGER  Specify the metrics update interval in seconds.
      --help              Show this message and exit.



Configure Control Socket
////////////////////////

The exporter uses Kea's control socket and the ``statistic-get-all`` request. Consult the documentation on how to set up
the control socket:

- http://kea.isc.org/docs/kea-guide.html#dhcp4-ctrl-channel
- http://kea.isc.org/docs/kea-guide.html#dhcp6-ctrl-channel

Permissions
///////////

Kea Exporter needs to be able to read and write on the socket, hence it's permissions might need to be modified
accordingly.