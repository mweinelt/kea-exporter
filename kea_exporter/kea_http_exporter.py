import requests

from .base_exporter import BaseExporter

class KeaHTTPExporter(BaseExporter):
    def __init__(self, target, **kwargs):
        super().__init__()

        self._target = target

        self.modules = []
        self.subnets = {}
        self.subnets6 = {}

        self.load_modules()

        self.load_subnets()


    def load_modules(self):
        r = requests.post(self._target, json = {'command': 'config-get'},
            headers={'Content-Type': 'application/json'})
        config= r.json()
        for module in (config[0]['arguments']['Control-agent']
            ['control-sockets']):
            if "dhcp" in module: # Does not support d2 metrics. # Does not handle ctrl sockets that are offline
                self.modules.append(module)


    def load_subnets(self):
        r = requests.post(self._target, json = {'command': 'config-get',
            'service': self.modules },
            headers={'Content-Type': 'application/json'})
        config = r.json()
        for module in config:
            for subnet in (module.get('arguments', {}).get('Dhcp4', {}).get('subnet4', {})):
                self.subnets.update( {subnet['id']: subnet} )
            for subnet in (module.get('arguments', {}).get('Dhcp6', {}).get('subnet6', {})):
                self.subnets6.update( {subnet['id']: subnet} )


    def update(self):
        # Reload subnets on update in case of configurational update
        self.load_subnets()
        # Note for future testing: pipe curl output to jq for an easier read
        r = requests.post(self._target, json = {'command':
            'statistic-get-all', 'arguments': { }, 'service': self.modules },
                headers={'Content-Type': 'application/json'})
        response = r.json()

        for index, module in enumerate(self.modules):
            if module == 'dhcp4':
                dhcp_version = self.DHCPVersion.DHCP4
                subnets = self.subnets
            elif module == 'dhcp6':
                dhcp_version = self.DHCPVersion.DHCP6
                subnets = self.subnets6
            else:
                continue

            arguments = response[index].get('arguments', {})
            
            self.parse_metrics(dhcp_version, arguments, subnets)