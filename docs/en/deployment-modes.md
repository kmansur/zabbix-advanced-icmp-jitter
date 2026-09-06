# Deployment architecture

**English** | [Português (Brasil)](../pt-BR/deployment-modes.md)

The project ships **one hybrid template**: `Advanced ICMP Ping with Jitter`.

## Primary path — native and scalable

Every minute Zabbix uses its native `SIMPLE` checks:

- `icmpping` for availability;
- `icmppingloss` for packet loss;
- `icmppingsec` in `avg` mode for average RTT.

These checks are handled by the Zabbix server/proxy ICMP pingers. Targets with compatible parameters can be grouped through `fping`, so the monitoring path that determines state, loss and average latency does not start one Python process per host.

## Advanced statistics — integrated in the same template

The same template retains one lower-frequency `EXTERNAL` item controlled by `{$ADV_ICMP_STATS_INTERVAL}` (default `5m`). It is used only for metrics the native ICMP pinger does not expose from the individual RTTs of the same packet batch:

- packet-to-packet jitter;
- RTT standard deviation;
- minimum and maximum RTT from the same sample batch.

If the advanced collector fails, `Collector error` alerts while availability, packet loss and average RTT continue through the native ICMP path and do not depend on Python.

## Scale

For larger deployments, keep the native core at `1m` and increase only `{$ADV_ICMP_STATS_INTERVAL}` to `10m` or `15m` when advanced statistics do not require high frequency. Device-state sensitivity remains around three minutes while external-check load can be reduced independently.
