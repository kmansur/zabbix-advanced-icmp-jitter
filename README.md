# Advanced ICMP Ping with Jitter

Zabbix 7.0 template for monitoring ICMP latency, packet loss, jitter, and RTT
standard deviation using `fping` and a Python external script.

This template is designed for network devices, links, servers, gateways, and
any host where ICMP reachability and latency stability matter.

## What This Template Measures

The template collects one ICMP probe batch and derives all metrics from the same
sample window. This avoids running multiple ping commands for the same host and
keeps the data internally consistent.

Collected metrics:

- Average ICMP response time.
- Minimum ICMP response time.
- Maximum ICMP response time.
- Packet loss percentage.
- Transmitted packet count.
- Received packet count.
- ICMP jitter.
- RTT standard deviation.
- Collector error state.
- Raw JSON output for troubleshooting.

## How It Works

The Zabbix template has one master external item:

```text
advanced_icmp_ping.py["{HOST.CONN}","{$ADV_FPING_POOL_COUNT}","{$ADV_FPING_INTERVAL_MS}","{$ADV_FPING_TIMEOUT_MS}"]
```

The script runs:

```sh
fping -q -C <count> -p <interval_ms> -t <timeout_ms> <host>
```

`fping -C` returns one RTT value per transmitted ICMP packet. The script parses
those RTT samples and returns JSON. All Zabbix metrics are dependent items that
use JSONPath preprocessing.

This design gives two useful benefits:

- One ICMP batch per update interval.
- All latency, loss, jitter, and deviation values come from the same packet set.

## Jitter Calculation

Jitter is calculated as the average absolute difference between consecutive
received RTT samples:

```text
jitter = average(abs(current_rtt - previous_rtt))
```

Example:

```text
RTTs:        10.0, 13.0, 11.0, 20.0
Differences:  3.0,  2.0,  9.0
Jitter:       4.667 ms
```

This is more precise than estimating jitter as `max - min`, because it measures
packet-to-packet variation inside the sample window.

Lost packets are not used as RTT values because there is no response time to
measure. They are still counted in `xmt`, `rcv`, and `loss`.

## Standard Deviation

RTT standard deviation measures how spread out the received RTT samples are
around their average.

Practical interpretation:

- Low `stddev`: latency is stable.
- High `stddev`: latency is irregular, even if the average looks acceptable.

Jitter and standard deviation are complementary:

- `jitter` shows packet-to-packet variation.
- `stddev` shows overall RTT dispersion during the batch.

## Files

- `Advanced ICMP Ping with Jitter.yaml` - Zabbix 7.0 template export.
- `advanced_icmp_ping.py` - Python external script used by the template.
- `LICENSE` - GNU General Public License v3.0.

## Requirements

- Zabbix 7.0 server or proxy.
- External scripts enabled in the Zabbix server/proxy configuration.
- Python 3.6 or newer.
- `fping` installed.
- The Zabbix server/proxy user must be able to execute `fping`.

## Install Dependencies

Debian/Ubuntu:

```sh
apt update
apt install python3 fping
```

RHEL/Rocky/AlmaLinux:

```sh
dnf install python3 fping
```

FreeBSD:

```sh
pkg install python3 fping
```

## Install The External Script

Copy the collector to the Zabbix external scripts directory:

```sh
cp advanced_icmp_ping.py /usr/lib/zabbix/externalscripts/
chmod +x /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

If your Zabbix installation uses another external scripts directory, check:

```sh
grep -i '^ExternalScripts' /etc/zabbix/zabbix_server.conf
grep -i '^ExternalScripts' /etc/zabbix/zabbix_proxy.conf
```

If the parameter is commented out, Zabbix uses its compiled default. Common
paths include:

```text
/usr/lib/zabbix/externalscripts
/usr/local/share/zabbix/externalscripts
```

## Test The Collector Manually

Run the script as the Zabbix user whenever possible:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Expected output format:

```json
{"error":"","xmt":20,"rcv":20,"loss":0.0,"min":10.1,"avg":12.65,"max":16.3,"jitter":1.678,"stddev":1.887,"rtts":[11.9,11.3],"target":"8.8.8.8"}
```

The `rtts` array in real output will contain all received RTT samples. It is
kept mainly for troubleshooting and visibility in the raw JSON item.

If there is a collector problem, the script still returns valid JSON:

```json
{"error":"fping command not found","xmt":0,"rcv":0,"loss":100,"min":0,"avg":0,"max":0,"jitter":0,"stddev":0,"rtts":[]}
```

The template includes a trigger for this condition.

## Import The Template

1. Open the Zabbix frontend.
2. Go to `Data collection` -> `Templates`.
3. Click `Import`.
4. Select `Advanced ICMP Ping with Jitter.yaml`.
5. Review import rules.
6. Import the template.
7. Link it to the desired hosts.

The template uses `{HOST.CONN}` as the target. Make sure the linked host has a
valid interface address or DNS name.

## Supported Target Formats

The collector supports targets accepted by `fping`, including:

- IPv4 addresses, such as `8.8.8.8`.
- DNS names, such as `example.com`.
- IPv6 addresses, such as `2001:4860:4860::8888`, when IPv6 routing and `fping`
  IPv6 support are available on the Zabbix server or proxy.

Manual IPv6 test:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 2001:4860:4860::8888 20 100 1000
```

If the host uses DNS, remember that `{HOST.CONN}` depends on the selected
interface connection mode in Zabbix. Confirm that the resolved target is the one
you expect.

## Default Macros

| Macro | Default | Meaning |
| --- | ---: | --- |
| `{$ADV_FPING_POOL_COUNT}` | `20` | Number of ICMP probes per batch. |
| `{$ADV_FPING_INTERVAL_MS}` | `100` | Delay between probes in milliseconds. |
| `{$ADV_FPING_TIMEOUT_MS}` | `1000` | Timeout per probe in milliseconds. |
| `{$ADV_ICMP_LOSS_WARN}` | `20` | Packet loss warning threshold in percent. |
| `{$ADV_ICMP_JITTER_WARN}` | `20` | Jitter warning threshold in milliseconds. |
| `{$ADV_ICMP_RESPONSE_TIME_WARN}` | `200` | Average latency warning threshold in milliseconds. |
| `{$ADV_ICMP_MAX_TIME_MULTIPLE}` | `30` | Warning threshold for max/min latency ratio. |
| `{$ADV_ICMP_STDDEV_WARN}` | `30` | RTT standard deviation threshold in milliseconds. |

The default collector settings send 20 probes spaced 100 ms apart. This gives a
measurement window of about 2 seconds and provides a good balance between jitter
precision and collection time.

## Tuning Recommendations

General WAN monitoring:

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=100
{$ADV_FPING_TIMEOUT_MS}=1000
{$ADV_ICMP_JITTER_WARN}=20
```

Low-latency LAN or datacenter monitoring:

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_ICMP_JITTER_WARN}=5
{$ADV_ICMP_STDDEV_WARN}=10
```

Internet links or higher-latency paths:

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=100
{$ADV_ICMP_JITTER_WARN}=30
{$ADV_ICMP_STDDEV_WARN}=50
```

Sensitive VoIP/video paths:

```text
{$ADV_FPING_POOL_COUNT}=30
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_ICMP_JITTER_WARN}=20
{$ADV_ICMP_STDDEV_WARN}=30
```

Higher probe counts improve jitter confidence, but also increase collection
duration. A rough estimate is:

```text
duration ~= pool_count * interval_ms
```

For example:

```text
20 probes * 100 ms = about 2 seconds
30 probes * 50 ms  = about 1.5 seconds
```

## Items

| Item | Key | Type |
| --- | --- | --- |
| ICMP raw JSON results | `advanced_icmp_ping.py[...]` | External |
| ICMP average response time | `advanced.ping.avg` | Dependent |
| ICMP minimum response time | `advanced.ping.min` | Dependent |
| ICMP maximum response time | `advanced.ping.max` | Dependent |
| ICMP packet loss | `advanced.ping.loss` | Dependent |
| ICMP packets sent | `advanced.ping.xmt` | Dependent |
| ICMP packets received | `advanced.ping.rcv` | Dependent |
| ICMP jitter | `advanced.ping.jitter` | Dependent |
| ICMP RTT standard deviation | `advanced.ping.stddev` | Dependent |
| ICMP collector error | `advanced.ping.error` | Dependent |

## Triggers

Enabled by default:

- `Unavailable by ICMP ping`
- `High ICMP ping loss`
- `High ICMP ping response time`
- `High ICMP ping jitter`
- `High ICMP ping time differences`
- `ICMP collector error`

Disabled by default:

- `Total Unavailable by ICMP ping`
- `High ICMP RTT standard deviation`

The standard deviation trigger is disabled by default because not every network
needs alerting on dispersion. Enable it for links where latency stability is
important.

## Troubleshooting

### Zabbix item says the script cannot be found

Check that the script is in the external scripts directory and executable:

```sh
ls -l /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

### Collector error: `fping command not found`

Install `fping` and confirm it is in the Zabbix user's `PATH`:

```sh
which fping
sudo -u zabbix fping -v
```

### Collector error: `unable to parse fping output`

Run the script manually and inspect the raw behavior:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Also confirm that `fping -q -C` works on the system:

```sh
sudo -u zabbix fping -q -C 5 -p 100 -t 1000 8.8.8.8
```

### All packets are lost

Check firewall policy, routing, and ICMP filtering. Some hosts deprioritize or
block ICMP while still serving TCP/UDP traffic.

### Collection is too slow

Reduce the probe count or interval:

```text
{$ADV_FPING_POOL_COUNT}=10
{$ADV_FPING_INTERVAL_MS}=100
```

Do not set the interval too low on busy Zabbix servers monitoring many hosts.

### Jitter looks too noisy

Increase the probe count:

```text
{$ADV_FPING_POOL_COUNT}=30
```

Use trigger windows such as `avg(...,5m)` instead of `last()` for jitter alerts.
The template already uses a 5-minute average for jitter.

## License and Attribution

This project is based on `AdvancedPING` by Dusan Priechodsky:

https://github.com/priechodsky/AdvancedPING

The original project is licensed under the GNU General Public License v3.0
GPL-3.0. This modified version is also released under GPL-3.0.

Modified by Karim Mansur / Net Tech.

See `LICENSE` for the full GPL-3.0 license text.

## Versioning

Template vendor:

```yaml
vendor:
  name: 'Net Tech'
  version: 1.0-5
```

Collector script:

```text
advanced_icmp_ping.py version 1.0.5
```

Every functional template change should increment `vendor.version`.
