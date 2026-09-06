# Metrics and dashboard

[English](metrics.md) | [Português (Brasil)](../pt-BR/metrics.md)

## Collection architecture

The template executes one ICMP batch per update. The master item calls the Python collector and receives JSON; all other items consume the same payload through dependent items and JSONPath.

This avoids multiple ping commands for the same host and keeps all metrics calculated from the same sample set.

## Items

| Item | Key | Type |
| --- | --- | --- |
| Advanced ICMP: raw JSON results | `advanced_icmp_ping.py[...]` | External |
| Advanced ICMP: average response time | `advanced.ping.avg` | Dependent |
| Advanced ICMP: minimum response time | `advanced.ping.min` | Dependent |
| Advanced ICMP: maximum response time | `advanced.ping.max` | Dependent |
| Advanced ICMP: packet loss | `advanced.ping.loss` | Dependent |
| Advanced ICMP: packets sent | `advanced.ping.xmt` | Dependent |
| Advanced ICMP: packets received | `advanced.ping.rcv` | Dependent |
| Advanced ICMP: jitter | `advanced.ping.jitter` | Dependent |
| Advanced ICMP: RTT standard deviation | `advanced.ping.stddev` | Dependent |
| Advanced ICMP: collector error | `advanced.ping.error` | Dependent |

Item names remain in English to stay consistent with the exports and avoid cosmetic changes that could confuse existing environments.

## Jitter calculation

Jitter is the average absolute difference between consecutive received RTT values:

```text
jitter = average(abs(current_rtt - previous_rtt))
```

Example:

```text
RTTs:        10.0, 13.0, 11.0, 20.0
Differences:  3.0,  2.0,  9.0
Jitter:       4.667 ms
```

Lost packets are excluded from RTT calculations because they have no response time. They are still included in `xmt`, `rcv`, and `loss`.

## RTT standard deviation

The collector calculates the population standard deviation of received replies.

Practical interpretation:

- low `stddev`: latency is concentrated and stable;
- high `stddev`: samples are widely dispersed even if the average still looks acceptable.

Jitter and standard deviation are complementary:

- `jitter` measures variation between consecutive replies;
- `stddev` measures overall dispersion across the RTT sample set.

## Raw JSON

The master item keeps the full JSON payload for troubleshooting. Example:

```json
{"error":"","xmt":20,"rcv":20,"loss":0.0,"min":10.1,"avg":12.65,"max":16.3,"jitter":1.678,"stddev":1.887,"rtts":[11.9,11.3],"target":"8.8.8.8"}
```

The `rtts` array helps inspect individual samples when required.

## Dashboard

The template includes the dashboard:

```text
Advanced ICMP
```

with the graph:

```text
Advanced ICMP: latency, loss, jitter and deviation
```

Raw JSON is not displayed on the default dashboard so the view remains focused on operational metrics.

The classic graph uses an upper limit of `200` to make host-to-host comparisons easier while avoiding clipping common WAN latency peaks.

![Advanced ICMP graph example](../images/advanced-icmp-ping.png)
