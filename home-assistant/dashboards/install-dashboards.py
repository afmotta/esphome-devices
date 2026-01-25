#!/usr/bin/env python3
"""
Install Climate Control Dashboards via Home Assistant API

This script installs all dashboards using the Home Assistant REST API,
eliminating the need to edit configuration.yaml and restart HA.

Requirements:
- Home Assistant running and accessible
- Long-lived access token (create in HA profile)

Usage:
    python3 install-dashboards.py --url http://homeassistant.local:8123 --token YOUR_TOKEN
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import urllib.request
import urllib.error
import yaml


class DashboardInstaller:
    def __init__(self, ha_url: str, token: str):
        self.ha_url = ha_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _api_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request to Home Assistant"""
        url = f"{self.ha_url}/api/{endpoint}"

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8') if data else None,
            headers=self.headers,
            method=method
        )

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code}: {e.reason}")
            print(f"Response: {e.read().decode('utf-8')}")
            raise
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
            raise

    def load_dashboard_yaml(self, filepath: Path) -> Dict[str, Any]:
        """Load dashboard YAML file and convert to Lovelace config"""
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        return config

    def create_dashboard(self, url_path: str, config: Dict[str, Any],
                        title: str, icon: str, show_in_sidebar: bool = True) -> Dict[str, Any]:
        """Create or update a dashboard"""

        dashboard_config = {
            'url_path': url_path,
            'title': title,
            'icon': icon,
            'show_in_sidebar': show_in_sidebar,
            'require_admin': False
        }

        # First, try to get existing dashboard
        try:
            existing = self._api_request('GET', f'lovelace/dashboards/{url_path}')
            # Dashboard exists, update it
            print(f"Updating existing dashboard: {title}")
            result = self._api_request('PUT', f'lovelace/dashboards/{url_path}', dashboard_config)

            # Update the dashboard config
            self._api_request('POST', f'lovelace/dashboards/{url_path}/config', config)
            return result

        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Dashboard doesn't exist, create it
                print(f"Creating new dashboard: {title}")
                result = self._api_request('POST', 'lovelace/dashboards', dashboard_config)

                # Set the dashboard config
                self._api_request('POST', f'lovelace/dashboards/{url_path}/config', config)
                return result
            else:
                raise

    def install_all_dashboards(self, dashboards_dir: Path):
        """Install all dashboards from the directory"""

        dashboards = [
            {
                'file': 'climate-overview.yaml',
                'url_path': 'climate-overview',
                'title': 'Climate Control',
                'icon': 'mdi:home-thermometer',
                'show_in_sidebar': True
            },
            {
                'file': 'ground-floor.yaml',
                'url_path': 'ground-floor',
                'title': 'Ground Floor',
                'icon': 'mdi:home-floor-0',
                'show_in_sidebar': False
            },
            {
                'file': 'first-floor.yaml',
                'url_path': 'first-floor',
                'title': 'First Floor',
                'icon': 'mdi:home-floor-1',
                'show_in_sidebar': False
            },
            {
                'file': 'second-floor.yaml',
                'url_path': 'second-floor',
                'title': 'Second Floor',
                'icon': 'mdi:home-floor-2',
                'show_in_sidebar': False
            },
            {
                'file': 'system-monitoring.yaml',
                'url_path': 'system-monitoring',
                'title': 'System Monitoring',
                'icon': 'mdi:monitor-dashboard',
                'show_in_sidebar': False
            }
        ]

        results = []
        for dashboard in dashboards:
            filepath = dashboards_dir / dashboard['file']

            if not filepath.exists():
                print(f"Warning: {filepath} not found, skipping...")
                continue

            try:
                config = self.load_dashboard_yaml(filepath)
                result = self.create_dashboard(
                    url_path=dashboard['url_path'],
                    config=config,
                    title=dashboard['title'],
                    icon=dashboard['icon'],
                    show_in_sidebar=dashboard['show_in_sidebar']
                )
                results.append({
                    'dashboard': dashboard['title'],
                    'status': 'success',
                    'result': result
                })
                print(f"✓ {dashboard['title']} installed successfully")
            except Exception as e:
                results.append({
                    'dashboard': dashboard['title'],
                    'status': 'error',
                    'error': str(e)
                })
                print(f"✗ {dashboard['title']} failed: {e}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description='Install Climate Control Dashboards via Home Assistant API'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Home Assistant URL (e.g., http://homeassistant.local:8123)'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Long-lived access token from Home Assistant'
    )
    parser.add_argument(
        '--dashboards-dir',
        type=Path,
        default=Path(__file__).parent,
        help='Directory containing dashboard YAML files'
    )

    args = parser.parse_args()

    installer = DashboardInstaller(args.url, args.token)

    print(f"Installing dashboards from: {args.dashboards_dir}")
    print(f"Home Assistant URL: {args.url}")
    print("-" * 60)

    results = installer.install_all_dashboards(args.dashboards_dir)

    print("-" * 60)
    print("\nInstallation Summary:")
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')

    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")

    if error_count > 0:
        print("\nErrors:")
        for result in results:
            if result['status'] == 'error':
                print(f"  - {result['dashboard']}: {result['error']}")
        sys.exit(1)
    else:
        print("\n✓ All dashboards installed successfully!")
        print(f"\nAccess your dashboards at: {args.url}/lovelace/climate-overview")


if __name__ == '__main__':
    main()
