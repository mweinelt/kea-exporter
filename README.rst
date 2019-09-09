kea-exporter
============

Prometheus Exporter for the ISC Kea DHCP Server.

From v0.4.0 on Kea >=1.3.0 is required, as the configuration, specifically
subnet information, will be read from the control socket.


Installation
------------

The latest stable version can be installed from PyPi:

::

    $ pip install kea-exporter


and upgraded with:

::

    $ pip install --upgrade kea-exporter

Features
--------

- DHCP4 & DHCP6 Metrics (tested against Kea 1.6.0)
- Configuration and statistics via control socket

Currently not working:

- Automatic config reload (through inotify)


Known Limitations
-----------------

The following features are not supported yet, help is welcome.

- HTTP REST API (as a means to query a Kea instance)
- Shared Networks
- Custom Subnet Identifiers

Usage
-----

::

    Usage: kea-exporter [OPTIONS] SOCKETS...

    Options:
      --address TEXT      Specify the address to bind against.
      --port INTEGER      Specify the port on which to listen.
      --interval INTEGER  Specify the metrics update interval in seconds.
      --version           Show the version and exit.
      --help              Show this message and exit.



Configure Control Socket
////////////////////////

The exporter uses Kea's control socket to request both configuration and 
statistics. Consult the documentation on how to set up the control socket:

- https://kea.readthedocs.io/en/latest/arm/dhcp4-srv.html#management-api-for-the-dhcpv4-server
- https://kea.readthedocs.io/en/latest/arm/dhcp6-srv.html#management-api-for-the-dhcpv6-server

Permissions
///////////

Kea Exporter needs to be able to read and write on the socket, hence it's
permissions might need to be modified accordingly.
