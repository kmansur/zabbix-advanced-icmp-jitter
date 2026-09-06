# Troubleshooting

[English](troubleshooting.md) | [Português (Brasil)](../pt-BR/troubleshooting.md)

## Zabbix reports that the script was not found

Confirm the path and permissions:

```sh
ls -l /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

The file must be readable and executable by the Zabbix process user.

Inside the repository, the source file is located at:

```text
scripts/advanced_icmp_ping.py
```

## `fping command not found`

Check whether `fping` is installed and available to the Zabbix user:

```sh
which fping
sudo -u zabbix fping -v
```

## `unable to parse fping output`

Run the collector manually:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Also inspect the output format returned directly by `fping`:

```sh
sudo -u zabbix fping -q -C 5 -p 100 -t 1000 8.8.8.8
```

The parser expects sample lines containing RTT numbers or `-` for lost packets.

## All packets appear lost

Check:

- routing to the target;
- firewall policies;
- ICMP blocking or rate limiting;
- IPv4/IPv6 connectivity for the target type;
- `fping` permissions/capabilities on the operating system.

Some devices rate-limit ICMP even while TCP/UDP services remain available.

## Collection takes too long

Reduce packet count or interval:

```text
{$ADV_FPING_POOL_COUNT}=10
{$ADV_FPING_INTERVAL_MS}=100
```

Avoid extremely low intervals on Zabbix servers that monitor many hosts.

## Jitter is too variable

Increase the number of samples:

```text
{$ADV_FPING_POOL_COUNT}=30
```

The default trigger already uses a 5-minute average to reduce noise from isolated samples.

## IPv6 does not work

Test `fping` directly as the Zabbix user and confirm IPv6 connectivity:

```sh
sudo -u zabbix fping -q -C 5 -p 100 -t 1000 2001:4860:4860::8888
```

Then test the collector:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 2001:4860:4860::8888 20 100 1000
```

The project parser includes a specific test for IPv6 addresses containing multiple `:` characters.

## Template does not import

Confirm that the YAML matches the Zabbix version:

```text
templates/zabbix-7.0/ -> zabbix_export.version: '7.0'
templates/zabbix-8.0/ -> zabbix_export.version: '8.0'
```

During development, run:

```sh
python tools/validate_templates.py
```

The currently maintained 8.0 export was tested on **Zabbix 8.0 Beta 2**. If a newer Beta, RC, or final release rejects the file, export the template again from that build and compare the structure before replacing the project file.

## Raw JSON diagnostics

Open the history of the master item `Advanced ICMP: raw JSON results` and inspect:

- `error`;
- `xmt`;
- `rcv`;
- `loss`;
- `rtts`.

An empty `error` field indicates that the collector completed without a detected operational error.
