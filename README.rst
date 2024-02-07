|license| |version|

.. |license| image:: https://img.shields.io/github/license/mweinelt/kea-exporter
   :alt: GitHub license
   :target: https://github.com/mweinelt/kea-exporter/blob/develop/LICENSE

.. |version| image:: https://img.shields.io/github/v/tag/mweinelt/kea-exporter
   :alt: GitHub tag (latest SemVer)

kea-exporter
============

Prometheus Exporter for the ISC Kea DHCP Server.

From v0.4.0 on Kea >=1.3.0 is required, as the configuration, specifically
subnet information, will be read from the control socket.

Installation
------------

.. image:: https://repology.org/badge/vertical-allrepos/kea-exporter.svg
   :alt: Package versions via repology.org

The latest stable version can always be installed from PyPi:

::

    $ pip install kea-exporter


and upgraded with:

::

    $ pip install --upgrade kea-exporter

Features
--------

- DHCP4 & DHCP6 Metrics (tested against Kea 1.6.0)
- Configuration and statistics via control socket or http api

Currently not working:

- Automatic config reload (through inotify)


Known Limitations
-----------------

The following features are not supported yet, help is welcome.

- Shared Networks
- Custom Subnet Identifiers

Usage
-----

::

    Usage: kea-exporter [OPTIONS] SOCKETS...

    Options:
    -m, --mode [socket|http]  Select mode.
    -a, --address TEXT        Specify the address to bind against.
    -p, --port INTEGER        Specify the port on which to listen.
    -i, --interval INTEGER    Specify the metrics update interval in seconds.
    -t, --target TEXT         Target address and port of Kea server, e.g.
                               http://kea.example.com:8080.
    --client-cert TEXT        Client certificate file path used in HTTP mode
                               with mTLS
    --client-key TEXT         Client key file path used in HTTP mode with mTLS
    --version                 Show the version and exit.
    --help                    Show this message and exit.



Configure Control Socket
////////////////////////

The exporter uses Kea's control socket to request both configuration and 
statistics. Consult the documentation on how to set up the control socket:

- https://kea.readthedocs.io/en/latest/arm/dhcp4-srv.html#management-api-for-the-dhcpv4-server
- https://kea.readthedocs.io/en/latest/arm/dhcp6-srv.html#management-api-for-the-dhcpv6-server

HTTPS
///////////
If you need to validate a self-signed certificate on a Kea instance, you can set `REQUESTS_CA_BUNDLE`
environment variable to a bundle CA path.

Permissions
///////////

Kea Exporter needs to be able to read and write on the socket, hence it's
permissions might need to be modified accordingly.

Grafana-Dashboard
/////////////////

A dashboard for this exporter is available at https://grafana.com/grafana/dashboards/12688.
