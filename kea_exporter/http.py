import requests

from kea_exporter import DHCPVersion


class KeaHTTPClient:
    def __init__(self, target, client_cert, client_key, **kwargs):
        super().__init__()

        self._target = target
        if client_cert and client_key:
            self._cert = (
                client_cert,
                client_key,
            )
        else:
            self._cert = None

        self.modules = []
        self.subnets = {}
        self.subnets6 = {}

        self.load_modules()
        self.load_subnets()

    def load_modules(self):
        r = requests.post(
            self._target,
            cert=self._cert,
            json={"command": "config-get"},
            headers={"Content-Type": "application/json"},
        )
        config = r.json()
        for module in config[0]["arguments"]["Control-agent"]["control-sockets"]:
            if "dhcp" in module:  # Does not support d2 metrics. # Does not handle ctrl sockets that are offline
                self.modules.append(module)

    def load_subnets(self):
        r = requests.post(
            self._target,
            cert=self._cert,
            json={"command": "config-get", "service": self.modules},
            headers={"Content-Type": "application/json"},
        )
        config = r.json()
        for module in config:
            for subnet in module.get("arguments", {}).get("Dhcp4", {}).get("subnet4", {}):
                self.subnets.update({subnet["id"]: subnet})
            for subnet in module.get("arguments", {}).get("Dhcp6", {}).get("subnet6", {}):
                self.subnets6.update({subnet["id"]: subnet})

    def stats(self):
        # Reload subnets on update in case of configurational update
        self.load_subnets()
        # Note for future testing: pipe curl output to jq for an easier read
        r = requests.post(
            self._target,
            cert=self._cert,
            json={
                "command": "statistic-get-all",
                "arguments": {},
                "service": self.modules,
            },
            headers={"Content-Type": "application/json"},
        )
        response = r.json()

        for index, module in enumerate(self.modules):
            if module == "dhcp4":
                dhcp_version = DHCPVersion.DHCP4
                subnets = self.subnets
            elif module == "dhcp6":
                dhcp_version = DHCPVersion.DHCP6
                subnets = self.subnets6
            else:
                continue

            arguments = response[index].get("arguments", {})

            yield dhcp_version, arguments, subnets
