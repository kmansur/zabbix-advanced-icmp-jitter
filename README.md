# Advanced ICMP Ping with Jitter

[![CI](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/ci.yml/badge.svg)](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/security.yml/badge.svg)](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/security.yml)

**English** | [Português (Brasil)](README.pt-BR.md)

Zabbix template for advanced ICMP monitoring with latency, packet loss, jitter, and RTT standard deviation. A single Python external check runs `fping`, returns JSON, and feeds dependent Zabbix items from the same probe batch.

## Compatibility

| Zabbix | Template | Status |
| --- | --- | --- |
| 7.0 | `templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml` | Supported |
| 8.0 | `templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml` | Tested on **Zabbix 8.0 Beta 2**; revalidated as new Beta/RC/final builds are tested |

The Zabbix 8.0 compatibility notes are documented in [docs/en/zabbix-8.0.md](docs/en/zabbix-8.0.md).

## Metrics

The template collects one ICMP batch and derives:

- average, minimum, and maximum RTT;
- packet loss;
- transmitted and received packet counts;
- jitter based on consecutive received RTT differences;
- population RTT standard deviation;
- collector error state;
- raw JSON for troubleshooting.

## Repository layout

```text
.github/                 GitHub workflows, Dependabot, PR and issue templates
docs/
├── en/                  English documentation
├── images/              Documentation images
└── pt-BR/               Brazilian Portuguese documentation
scripts/                 Production Zabbix external collector
templates/
├── zabbix-7.0/          Zabbix 7.0 export
└── zabbix-8.0/          Zabbix 8.0 export
tests/                   Unit tests and fping fixtures
tools/                   Repository and template validation tools
```

## Quick start

Install the collector dependencies on the Zabbix Server or Proxy.

Debian/Ubuntu:

```sh
apt update
apt install python3 fping
```

Install the collector in the Zabbix external scripts directory:

```sh
cp scripts/advanced_icmp_ping.py /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
chmod +x /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

Test it as the Zabbix user:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Then import the YAML that matches the target Zabbix major/minor version.

## Documentation

English:

- [Overview](docs/en/README.md)
- [Installation](docs/en/installation.md)
- [Configuration and macros](docs/en/configuration.md)
- [Metrics and dashboard](docs/en/metrics.md)
- [Triggers](docs/en/triggers.md)
- [Tuning](docs/en/tuning.md)
- [Troubleshooting](docs/en/troubleshooting.md)
- [Zabbix 8.0 compatibility](docs/en/zabbix-8.0.md)
- [Versioning](docs/en/versioning.md)

The Brazilian Portuguese documentation is available under [docs/pt-BR/](docs/pt-BR/README.md).

## Development

Install development dependencies:

```sh
python -m pip install -r requirements-dev.txt
```

Run the same checks used by CI:

```sh
python -m compileall -q scripts tools tests
ruff check scripts tools tests
ruff format --check scripts tools tests
pytest -q
python tools/validate_templates.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development and Zabbix export workflow.

## Versioning

The current tested template version remains `1.0-10` to preserve the existing exports during repository-only reorganization. The next functional release will transition to Semantic Versioning (`MAJOR.MINOR.PATCH`).

The release workflow requires `VERSION`, the Zabbix `vendor.version`, the Git tag, and the GitHub Release version to agree.

## License and attribution

This project is based on `AdvancedPING` by Dusan Priechodsky and is distributed under the GNU General Public License v3.0 (GPL-3.0).

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).

Maintained modifications: Karim Mansur / Net Tech.
