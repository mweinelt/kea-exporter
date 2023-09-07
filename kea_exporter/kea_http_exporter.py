import sys
import requests

import click

from .base_exporter import BaseExporter


class KeaHTTPExporter(BaseExporter):
    def __init__(self, target, **kwargs):
        super().__init__()
        self._target = target

        self.modules = []
        self.subnets = {}
        self.subnets6 = {}

        self.subnet_missing_info_sent = {"dhcp4": [], "dhcp6": []}

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
                self.subnets.update( {subnet['id']: subnet['subnet']} )
            for subnet in (module.get('arguments', {}).get('Dhcp6', {}).get('subnet6', {})):
                self.subnets6.update( {subnet['id']: subnet['subnet']} )


    def update(self):
        # Reload subnets on update in case of configurational update
        self.load_subnets()
        # Note for future testing: pipe curl output to jq for an easier read
        r = requests.post(self._target, json = {'command':
            'statistic-get-all', 'arguments': { }, 'service': self.modules },
                headers={'Content-Type': 'application/json'})
        self.parse_metrics(r.json())


    def parse_metrics(self, response):
        for index, module in enumerate(self.modules):
            for key, data in response[index].get('arguments', {}).items():
                if module == 'dhcp4':
                    if key in self.metrics_dhcp4_global_ignore:
                        continue
                elif module == 'dhcp6':
                    if key in self.metrics_dhcp6_global_ignore:
                        continue
                else:
                    continue

                value, timestamp = data[0]
                labels = {}
                if key.startswith('subnet['):
                    match = self.subnet_pattern.match(key)

                    if match:
                        subnet_id = int(match.group('subnet_id'))

                        key = match.group('metric')
                        if module == 'dhcp4':
                            subnet = self.subnets.get(subnet_id)
                        elif module == 'dhcp6':
                            subnet = self.subnets6.get(subnet_id)
                        else:
                            continue
                    
                        try:
                            subnet = self.subnets[subnet_id]
                        except KeyError:
                            if subnet_id not in self.subnet_missing_info_sent.get(module, []):
                                self.subnet_missing_info_sent.get(module, []).append(subnet_id)
                                click.echo(
                                    f"The subnet with id {subnet_id} on module {module} appeared in statistics "
                                    f"but is not part of the configuration anymore! Ignoring.",
                                    file=sys.stderr
                                )
                            continue

                        labels['subnet'] = subnet
                        labels['subnet_id'] = subnet_id
                    else:
                        print('subnet pattern failed for metric: {0}'.format(
                            key), file=sys.stderr)

                if module == 'dhcp4':
                    metrics_map = self.metrics_dhcp4_map
                    metrics = self.metrics_dhcp4
                elif module == 'dhcp6':
                    metrics_map = self.metrics_dhcp6_map
                    metrics = self.metrics_dhcp6
                else:
                    continue

                try:
                    metric_info = metrics_map[key]
                except KeyError:
                    if key not in self.unhandled_metrics:
                        click.echo(f"Unhandled metric '{key}', please open an issue at https://github.com/mweinelt/kea-exporter/issues")
                        self.unhandled_metrics.add(key)
                    continue

                metric = metrics[metric_info['metric']]

                # merge static and dynamic labels
                labels.update(metric_info.get('labels', {}))

                # export labels and value
                metric.labels(**labels).set(value)