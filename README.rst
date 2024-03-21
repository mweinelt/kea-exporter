|license| |version| |pypi_version| |pypi_downloads|

.. |license| image:: https://img.shields.io/github/license/mweinelt/kea-exporter
   :alt: GitHub license
   :target: https://github.com/mweinelt/kea-exporter/blob/develop/LICENSE

.. |version| image:: https://img.shields.io/github/v/tag/mweinelt/kea-exporter
   :alt: GitHub tag (latest SemVer)

.. |pypi_version| image:: https://img.shields.io/pypi/v/kea-exporter
   :alt: PyPI - Version

.. |pypi_downloads| image:: https://img.shields.io/pypi/dm/kea-exporter
   :alt: PyPI - Downloads

kea-exporter
============

Prometheus Exporter for the ISC Kea DHCP Server.

From v0.4.0 on Kea >=1.3.0 is required, as the configuration, specifically
subnet information, will be read from the control socket.

Installation
------------

.. image:: https://repology.org/badge/vertical-allrepos/kea-exporter.svg
   :alt: Package versions via repology.org
   :target: https://repology.org/project/kea-exporter/versions

The latest stable version can always be installed from PyPi:

::

    $ pip install kea-exporter


and upgraded with:

::

    $ pip install --upgrade kea-exporter

Docker
--------

A docker image is available and can be configured with environment variables see usage section

::

    $ docker pull ghcr.io/mweinelt/kea-exporter

Features
--------

- DHCP4 & DHCP6 Metrics (tested against Kea 2.4.1)
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

Pass one or multiple Unix Domain Socket path or HTTP Control-Agent URLs
to the `kea-exporter` executable. All other options are optional.

::

	Usage: python -m kea_exporter [OPTIONS] TARGETS...

	Options:
	  -a, --address TEXT      Address that the exporter binds to.
	  -p, --port INTEGER      Port that the exporter binds to.
	  -i, --interval INTEGER  Minimal interval between two queries to Kea in
	                          seconds.
	  --client-cert PATH      Path to client certificate used to in HTTP requests
	  --client-key PATH       Path to client key used in HTTP requests
	  --version               Show the version and exit.
	  --help                  Show this message and exit.

You can also configure the exporter using environment variables:

::

   export ADDRESS="0.0.0.0"
   export PORT="9547"
   export INTERVAL="7.5"
   export TARGETS="http://router.example.com:8000"
   export CLIENT_CERT="/etc/kea-exporter/client.crt"
   export CLIENT_KEY="/etc/kea-exporter/client.key"


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
