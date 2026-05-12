# Changelog

All notable changes to `Advanced ICMP Ping with Jitter` are documented here.

The template version is stored in the Zabbix export under:

```yaml
vendor:
  name: 'Net Tech'
  version: x.y-z
```

## [1.0-10] - 2026-05-11

### Changed

- Enabled the long ICMP unavailability trigger as an escalation signal.
- Renamed `Advanced ICMP: Total unavailable by ICMP ping` to
  `Advanced ICMP: Long unavailable by ICMP ping` for clearer intent.
- Changed unavailable trigger expressions from `last(...,#N)=0` to
  `max(...,#N)=0` so the short and long outage triggers evaluate full windows
  of consecutive failed collections.
- Added a dependency from `Advanced ICMP: Unavailable by ICMP ping` to
  `Advanced ICMP: Long unavailable by ICMP ping` to avoid duplicate visible
  problems during extended outages.
- Documented the automatic recovery behavior for unavailable triggers.
- Updated the template vendor version to `1.0-10`.

## [1.0-9] - 2026-05-11

### Changed

- Added the `Advanced ICMP:` prefix to visible item names to make them easier
  to identify in Zabbix views shared with standard ICMP monitoring.
- Kept item keys unchanged to preserve history, trigger references, and
  compatibility.
- Updated the README item table with the new visible item names.
- Updated the template vendor version to `1.0-9`.

## [1.0-8] - 2026-05-11

### Fixed

- Fixed Zabbix import validation for graph `yaxismin` and `yaxismax` by
  exporting fixed axis values as strings.
- Updated the template vendor version to `1.0-8`.

## [1.0-7] - 2026-05-11

### Changed

- Added the `Advanced ICMP:` prefix to trigger names to avoid confusion with
  standard ICMP triggers in global Zabbix views.
- Renamed the default dashboard to `Advanced ICMP`.
- Renamed the graph to `Advanced ICMP: latency, loss, jitter and deviation`.
- Set the classic graph fixed Y-axis range to `0-200` to preserve visual
  comparison across hosts while preventing common WAN latency peaks from being
  clipped.
- Updated the README with the fixed-axis behavior and renamed trigger examples.
- Updated the template vendor version to `1.0-7`.

## [1.0-6] - 2026-05-01

### Changed

- Removed the `itemhistory` widget for the raw JSON master item from the default
  dashboard.
- Increased the default graph widget height so the dashboard focuses on visual
  ICMP metrics.
- Kept `ICMP raw JSON results` as an item for troubleshooting.
- Updated the README to explain why raw JSON is not shown on the dashboard.
- Updated the template vendor version to `1.0-6`.

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
