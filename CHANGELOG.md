# Changelog

All notable changes to `Advanced ICMP Ping with Jitter` are documented here.

The template version is stored in the Zabbix export under:

```yaml
vendor:
  name: 'Net Tech'
  version: x.y-z
```

## [1.0-5] - 2026-05-01

### Fixed

- Added IPv6-safe parsing for `fping -q -C` output.
- Changed the parser to split the `fping` output from the right side using
  ` " : " ` so IPv6 addresses are not broken by internal colons.
- Added a guard to the `High ICMP ping time differences (Min/Max)` trigger to
  avoid division by zero when the average minimum RTT is `0`.

### Changed

- Updated `advanced_icmp_ping.py` to version `1.0.5`.
- Documented IPv4, DNS, and IPv6 target support in the README.
- Added a manual IPv6 collector test example.

## [1.0-4] - 2026-05-01

### Changed

- Removed dashed graph lines from the latency graph.
- Changed the ICMP minimum response time graph item to `GRADIENT_LINE`.
- Kept maximum latency, jitter, and standard deviation as regular lines.
- Updated the template vendor version to `1.0-4`.

## [1.0-3] - 2026-05-01

### Changed

- Expanded the README with detailed installation, collector behavior, tuning,
  item, trigger, troubleshooting, and licensing documentation.
- Updated `advanced_icmp_ping.py` to version `1.0.3`.
- Updated the template vendor version to `1.0-3`.

## [1.0-2] - 2026-05-01

### Added

- Added the full GNU General Public License v3.0 text as `LICENSE`.
- Added attribution to the original `AdvancedPING` project by Dusan Priechodsky.
- Added GPL-3.0 notices to the README, template description, and Python
  collector header.

### Changed

- Updated `advanced_icmp_ping.py` to version `1.0.2`.
- Updated the template vendor version to `1.0-2`.

## [1.0-1] - 2026-05-01

### Added

- Added `ICMP collector error` dependent item.
- Added `ICMP collector error` trigger.
- Added `ICMP RTT standard deviation` trigger, disabled by default.
- Added `{$ADV_ICMP_STDDEV_WARN}` macro.
- Added README with installation, macros, trigger, and collector notes.

### Changed

- Updated item names to clearer ICMP-focused labels.
- Updated graph and dashboard labels.
- Changed packet loss trigger dependencies to use `{$ADV_ICMP_LOSS_WARN}`
  instead of a hardcoded threshold.
- Updated successful collector JSON payloads to include `"error": ""`.
- Updated `advanced_icmp_ping.py` to version `1.0.1`.
- Updated the template vendor version to `1.0-1`.

## [1.0-0] - 2026-05-01

### Added

- Initial Zabbix 7.0 template: `Advanced ICMP Ping with Jitter`.
- Python collector: `advanced_icmp_ping.py`.
- Master external item returning JSON.
- Dependent items for:
  - average RTT
  - minimum RTT
  - maximum RTT
  - packet loss
  - transmitted packets
  - received packets
  - jitter
  - RTT standard deviation
- Jitter calculation based on the average absolute difference between
  consecutive received RTT samples.
- Default collector macros:
  - `{$ADV_FPING_POOL_COUNT}=20`
  - `{$ADV_FPING_INTERVAL_MS}=100`
  - `{$ADV_FPING_TIMEOUT_MS}=1000`
- Default alert macros:
  - `{$ADV_ICMP_LOSS_WARN}=20`
  - `{$ADV_ICMP_JITTER_WARN}=20`
  - `{$ADV_ICMP_RESPONSE_TIME_WARN}=200`
  - `{$ADV_ICMP_MAX_TIME_MULTIPLE}=30`
- Dashboard and graph for latency, loss, jitter, and deviation.

## Repository Maintenance

### 2026-05-01

- Removed the unused legacy shell helper `Advanced_ping.sh`.
- Renamed the project directory from `Adcanced ICMP Ping with Jitter` to
  `Advanced ICMP Ping with Jitter`.
- Added `.gitignore` entries for Python cache files:
  - `__pycache__/`
  - `*.pyc`
