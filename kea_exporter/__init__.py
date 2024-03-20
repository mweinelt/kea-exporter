from enum import Enum

__project__ = "kea-exporter"
__version__ = "0.6.2"


class DHCPVersion(Enum):
    DHCP4 = 1
    DHCP6 = 2
