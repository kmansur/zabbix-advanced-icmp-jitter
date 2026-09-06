# Installation

[English](installation.md) | [Português (Brasil)](../pt-BR/installation.md)

## Requirements

- Zabbix Server or Zabbix Proxy compatible with one of the maintained exports;
- Python 3.9 or newer on the server/proxy that will execute the external check;
- `fping` installed;
- `ExternalScripts` configured or the installation default path in use;
- the Zabbix process user must be allowed to execute `fping` and the collector.

Project CI tests Python 3.9 and current Python releases to prevent regressions in the maintained collector.

## Installing dependencies

### Debian / Ubuntu

```sh
apt update
apt install python3 fping
```

### RHEL / Rocky Linux / AlmaLinux

```sh
dnf install python3 fping
```

### FreeBSD

```sh
pkg install python3 fping
```

## Installing the collector

Inside the repository, the collector is located at:

```text
scripts/advanced_icmp_ping.py
```

Copy it to the Zabbix external scripts directory. Common Linux example:

```sh
cp scripts/advanced_icmp_ping.py /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
chmod +x /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

To check whether `ExternalScripts` is explicitly configured:

```sh
grep -i '^ExternalScripts' /etc/zabbix/zabbix_server.conf
grep -i '^ExternalScripts' /etc/zabbix/zabbix_proxy.conf
```

Common paths include:

```text
/usr/lib/zabbix/externalscripts
/usr/local/share/zabbix/externalscripts
```

## Manual collector test

Whenever possible, test using the same account that runs Zabbix:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 250 250
```

Example of valid output:

```json
{"error":"","xmt":20,"rcv":20,"loss":0.0,"min":10.1,"avg":12.65,"max":16.3,"jitter":1.678,"stddev":1.887,"rtts":[11.9,11.3],"target":"8.8.8.8"}
```

If collection fails, the script still returns valid JSON so dependent items do not receive malformed content. Example:

```json
{"error":"fping command not found","xmt":0,"rcv":0,"loss":100,"min":0,"avg":0,"max":0,"jitter":0,"stddev":0,"rtts":[]}
```

The maintained 1.1.0 candidate enforces `timeout <= interval` in `fping` count mode and rejects probe configurations whose estimated runtime exceeds the collector safety budget.

## Importing the template

In the Zabbix frontend:

1. open `Data collection` > `Templates`;
2. click `Import`;
3. choose the file that matches the Zabbix version;
4. review the changes shown by the frontend;
5. complete the import;
6. link the template to the required hosts.

Maintained files:

```text
templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml
templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml
```

The 8.0 export was tested on **Zabbix 8.0 Beta 2** and will be revalidated as new builds are tested.

### Migrating from legacy AdvancedPING

If the host previously used the original AdvancedPING template or an older derivative, review the [legacy AdvancedPING upgrade guide](legacy-advancedping-upgrade.md) before removing or linking templates. In particular, Zabbix **Unlink** preserves inherited entities on the host, while **Unlink and clear** removes them; legacy local triggers can otherwise coexist with the maintained `Advanced ICMP:` triggers.

## IPv6 test

The collector accepts addresses supported by the installed `fping`. For IPv6:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 2001:4860:4860::8888 20 250 250
```

The server/proxy must have IPv6 connectivity and the installed `fping` must provide appropriate IPv6 support.
