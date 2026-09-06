# Deployment modes

[English](deployment-modes.md) | [Português (Brasil)](../pt-BR/deployment-modes.md)

The project provides two complementary monitoring modes.

## Advanced ICMP Ping — native, scalable default

Use `advanced-icmp-ping.yaml` for broad deployment. It uses Zabbix `SIMPLE` checks:

- `icmpping` for reachability;
- `icmppingloss` for packet loss;
- `icmppingsec` in `avg` mode for average RTT.

All three run through the Zabbix server/proxy ICMP pinger. Targets with identical parameters can be grouped and checked by `fping` in parallel, avoiding a Python process per monitored host. The default update interval is one minute, with short unavailability at about 3 minutes and long unavailability at about 30 minutes.

## Advanced ICMP Ping with Jitter — selective advanced statistics

Use `advanced-icmp-ping-with-jitter.yaml` where you need individual RTT samples, jitter, population standard deviation, or min/max from the same packet batch. Its master item is an `EXTERNAL` check: the Zabbix server/proxy starts the Python collector, which starts `fping`, for each linked host and collection cycle.

Typical selective targets include WAN gateways, site-to-site links, firewalls, edge routers, voice/video paths, and links under troubleshooting.

Do not link both templates to the same host unless you intentionally want both native baseline monitoring and the additional external statistical workload.
