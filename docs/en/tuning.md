# Tuning

[English](tuning.md) | [Português (Brasil)](../pt-BR/tuning.md)

Ideal values depend on link characteristics, the number of monitored hosts, and the desired alert sensitivity.

## General WAN monitoring

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=250
{$ADV_FPING_TIMEOUT_MS}=250
{$ADV_ICMP_JITTER_WARN}=20
```

This is the project default profile and provides a good balance between batch duration and sample count.

## Low-latency LAN or datacenter

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_FPING_TIMEOUT_MS}=50
{$ADV_ICMP_JITTER_WARN}=5
{$ADV_ICMP_STDDEV_WARN}=10
```

Use lower thresholds only when the network actually has very low latency and variation.

## Internet or higher-latency paths

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=100
{$ADV_FPING_TIMEOUT_MS}=100
{$ADV_ICMP_JITTER_WARN}=30
{$ADV_ICMP_STDDEV_WARN}=50
```

## Voice, video, or variation-sensitive applications

```text
{$ADV_FPING_POOL_COUNT}=30
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_FPING_TIMEOUT_MS}=50
{$ADV_ICMP_JITTER_WARN}=20
{$ADV_ICMP_STDDEV_WARN}=30
```

Increasing the packet count improves the number of samples available for jitter and standard deviation, but also increases collection duration and cost.

## Approximate duration

```text
duration ~= packet_count * interval_ms
```

Examples:

```text
20 packets * 100 ms = approximately 2 seconds
30 packets * 50 ms  = approximately 1.5 seconds
```

The actual Python process timeout includes additional margin over the expected `fping` execution time.

## Environment scale

For broad ICMP availability, packet-loss and average-RTT monitoring, prefer the `Advanced ICMP Ping` native template. Zabbix can batch targets that share identical ICMP parameters through dedicated pinger processes. Reserve `Advanced ICMP Ping with Jitter` for selected paths where jitter and RTT standard deviation justify a per-host external collector.

On servers or proxies monitoring many hosts with the jitter template:

- avoid extremely low intervals;
- consider distributing collection across proxies;
- monitor external-check poller utilization;
- increase `POOL_COUNT` only when the precision gain justifies the cost;
- prefer average windows in triggers instead of alerting on a single sample.

## Trigger tuning

Before lowering thresholds, observe normal network behavior for a few days. In particular:

- `{$ADV_ICMP_JITTER_WARN}` should reflect the path's normal variation;
- `{$ADV_ICMP_RESPONSE_TIME_WARN}` should account for distance and link type;
- `{$ADV_ICMP_LOSS_WARN}` should separate transient loss from operational degradation;
- `{$ADV_ICMP_STDDEV_WARN}` is most useful on links where stability matters as much as average latency.

The standard deviation trigger is disabled by default to avoid noise in environments where the metric is only informational.

## Retention

The native template defaults to 30 days of raw history. The jitter template currently keeps 90 days for numeric metrics and 1 hour for raw JSON. Reduce raw history where database scale is more important than high-resolution forensic analysis; numeric trends preserve long-term behavior at much lower storage cost.
