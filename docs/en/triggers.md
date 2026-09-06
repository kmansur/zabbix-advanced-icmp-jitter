# Triggers

[English](triggers.md) | [Português (Brasil)](../pt-BR/triggers.md)

## Enabled by default

- `Advanced ICMP: Unavailable by ICMP ping`;
- `Advanced ICMP: Long unavailable by ICMP ping`;
- `Advanced ICMP: High packet loss`;
- `Advanced ICMP: High response time`;
- `Advanced ICMP: High jitter`;
- `Advanced ICMP: High time differences (Min/Max)`;
- `Advanced ICMP: Collector error`.

## Disabled by default

- `Advanced ICMP: High RTT standard deviation`.

The standard deviation trigger is disabled by default because not every network needs dispersion-based alerting. It can be enabled on links where latency stability matters.

## Short unavailability

The problem is raised when no ICMP replies are received during the last 3 batches:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#3)=0
```

Default severity: `HIGH`.

## Long unavailability

The escalation condition requires 30 consecutive batches without a reply:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#30)=0
```

Default severity: `DISASTER`.

The short outage trigger depends on the long outage trigger. When the outage grows into the long condition, that dependency avoids two visible problems representing the same failure.

Both triggers recover automatically when the expression becomes false and replies return within the evaluated window.

## Packet loss

```text
last(/Advanced ICMP Ping with Jitter/advanced.ping.loss,#2)>{$ADV_ICMP_LOSS_WARN}
```

The threshold is controlled by `{$ADV_ICMP_LOSS_WARN}`.

## High average latency

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.avg,5m)>{$ADV_ICMP_RESPONSE_TIME_WARN}
```

This trigger depends on high loss and unavailability to reduce derived alerts when the primary cause is severe packet loss or complete outage.

## High jitter

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.jitter,5m)>{$ADV_ICMP_JITTER_WARN}
```

The 5-minute average reduces alerts caused by a single isolated sample.

## High difference between minimum and maximum RTT

The expression compares the average maximum RTT with the average minimum RTT and protects against division by zero:

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.min,5m)>0 and avg(/Advanced ICMP Ping with Jitter/advanced.ping.max,5m)/avg(/Advanced ICMP Ping with Jitter/advanced.ping.min,5m)>{$ADV_ICMP_MAX_TIME_MULTIPLE}
```

## High standard deviation

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.stddev,5m)>{$ADV_ICMP_STDDEV_WARN}
```

This trigger is `DISABLED` in the default export.

## Collector error

```text
last(/Advanced ICMP Ping with Jitter/advanced.ping.error)<>""
```

It reports operational problems such as a missing `fping` command, command timeout, or output that the parser cannot recognize.
