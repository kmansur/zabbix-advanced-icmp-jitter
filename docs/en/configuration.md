# Configuration and macros

[English](configuration.md) | [Português (Brasil)](../pt-BR/configuration.md)

## Monitored target

The master item uses:

```text
{HOST.CONN}
```

Therefore, the effective target depends on the interface selected on the Zabbix host and whether that interface connects by IP or DNS.

Collector target formats, as long as they are accepted by the installed `fping`:

- IPv4, for example `8.8.8.8`;
- DNS, for example `example.com`;
- IPv6, for example `2001:4860:4860::8888`.

## Master item

The key used by the maintained exports is:

```text
advanced_icmp_ping.py["{HOST.CONN}","{$ADV_FPING_POOL_COUNT}","{$ADV_FPING_INTERVAL_MS}","{$ADV_FPING_TIMEOUT_MS}"]
```

Parameters are positional because Zabbix passes macro values directly to the external script.

## Default macros

| Macro | Default | Purpose |
| --- | ---: | --- |
| `{$ADV_FPING_POOL_COUNT}` | `20` | Number of ICMP probes per batch. |
| `{$ADV_FPING_INTERVAL_MS}` | `100` | Interval between probes, in milliseconds. |
| `{$ADV_FPING_TIMEOUT_MS}` | `1000` | Per-probe timeout, in milliseconds. |
| `{$ADV_ICMP_LOSS_WARN}` | `20` | Packet loss warning threshold, in %. |
| `{$ADV_ICMP_JITTER_WARN}` | `20` | Jitter warning threshold, in ms. |
| `{$ADV_ICMP_RESPONSE_TIME_WARN}` | `200` | Average latency warning threshold, in ms. |
| `{$ADV_ICMP_MAX_TIME_MULTIPLE}` | `30` | Threshold for the max/min RTT ratio. |
| `{$ADV_ICMP_STDDEV_WARN}` | `30` | RTT standard deviation warning threshold, in ms. |

## Collector safety limits

The collector validates and clamps received values to prevent accidentally tiny, negative, or excessively large parameters:

- packet count: minimum `2`, maximum `100`;
- interval: minimum `20 ms`, maximum `60000 ms`;
- timeout: minimum `50 ms`, maximum `60000 ms`.

Invalid values fall back to the collector's internal defaults.

## Measurement window

A simple approximation of batch duration is:

```text
duration ~= packet_count * interval_ms
```

Default example:

```text
20 packets * 100 ms = approximately 2 seconds
```

The Python process timeout includes additional margin so a stuck `fping` process does not occupy a Zabbix poller indefinitely.

## Choosing the export

Always use the directory that matches the Zabbix major/minor version:

```text
templates/zabbix-7.0/
templates/zabbix-8.0/
```

The repository validator prevents a YAML file from declaring a version different from the directory version.
