# Advanced ICMP Ping with Jitter — English

**English** | [Português (Brasil)](../pt-BR/README.md)

Zabbix template for advanced ICMP monitoring including latency, packet loss, jitter, and RTT standard deviation using `fping` and an external Python collector.

## Compatibility

| Zabbix | File | Status |
| --- | --- | --- |
| 7.0 | `templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml` | Supported |
| 8.0 | `templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml` | Tested on **Zabbix 8.0 Beta 2**; revalidated as new Beta, RC, and final builds are tested |

The collector is shared by all maintained versions:

```text
scripts/advanced_icmp_ping.py
```

## How it works

The template has a master `External check` item:

```text
advanced_icmp_ping.py["{HOST.CONN}","{$ADV_FPING_POOL_COUNT}","{$ADV_FPING_INTERVAL_MS}","{$ADV_FPING_TIMEOUT_MS}"]
```

The collector runs a single `fping -C` batch, parses each RTT sample, and returns JSON. All remaining items are dependent items that use JSONPath, so latency, loss, jitter, and standard deviation are calculated from the same packet set.

## Documentation

- [Installation](installation.md)
- [Upgrading from legacy AdvancedPING](legacy-advancedping-upgrade.md)
- [Configuration and macros](configuration.md)
- [Metrics and dashboard](metrics.md)
- [Triggers](triggers.md)
- [Tuning](tuning.md)
- [Troubleshooting](troubleshooting.md)
- [Zabbix 8.0 compatibility](zabbix-8.0.md)
- [Versioning](versioning.md)

## Project layout

```text
.github/                 CI, security, Dependabot, and GitHub templates
docs/
├── en/                  English documentation
├── images/              Documentation images
└── pt-BR/               Brazilian Portuguese documentation
scripts/                 Production external collector
templates/
├── zabbix-7.0/          Zabbix 7.0 export
└── zabbix-8.0/          Zabbix 8.0 export
tests/                   Unit tests and fping fixtures
tools/                   Semantic template validation
```

## Collected metrics

- average, minimum, and maximum RTT;
- packet loss;
- transmitted and received packets;
- jitter between consecutive replies;
- population RTT standard deviation;
- collector error;
- raw JSON for diagnostics.

## Graph example

![Advanced ICMP graph example](../images/advanced-icmp-ping.png)

## Development and validation

Local checks:

```sh
python -m pip install -r requirements-dev.txt
python -m compileall -q scripts tools tests
ruff check scripts tools tests
ruff format --check scripts tools tests
pytest -q
python tools/validate_templates.py
```

The validator checks the version declared by each YAML file and semantic parity across maintained exports without requiring identical serialization between Zabbix versions.

See also [CONTRIBUTING.md](../../CONTRIBUTING.md), [SECURITY.md](../../SECURITY.md), [CHANGELOG.md](../../CHANGELOG.md), and [NOTICE.md](../../NOTICE.md).
