# Upgrading from legacy AdvancedPING

[English](legacy-advancedping-upgrade.md) | [Português (Brasil)](../pt-BR/legacy-advancedping-upgrade.md)

This guide is intended for environments that previously used the original/legacy `AdvancedPING` template or an older derivative and are moving to **Advanced ICMP Ping with Jitter**.

The current project keeps the historical attribution to [AdvancedPING](https://github.com/priechodsky/AdvancedPING), but its template objects, trigger names, dependencies, tags, defaults, and validation rules have evolved.

## Why legacy objects may remain on a host

Zabbix provides two different ways to remove a linked template from a host:

- **Unlink** removes the template association but preserves inherited entities such as items, triggers, graphs, low-level discovery rules, and web scenarios on the host;
- **Unlink and clear** removes the association and removes the inherited entities as well.

Official references:

- [Zabbix 8.0 — Linking/unlinking templates](https://www.zabbix.com/documentation/8.0/en/manual/config/templates/linking)
- [Zabbix current — Configuring a host](https://www.zabbix.com/documentation/current/en/manual/config/hosts/host)

If a legacy AdvancedPING template was removed using only **Unlink**, old entities can remain as local host objects even after the new template is linked. This may result in duplicate or conflicting triggers.

## Typical legacy signatures

Legacy objects may use the same `advanced.ping.*` item keys while having older names or expressions. Examples seen in older AdvancedPING configurations include:

```text
Unavailable by ICMP ping
High ICMP ping loss
```

An older availability expression may look like:

```text
last(/<host>/advanced.ping.rcv,#3)=0
```

The maintained 1.1.0 candidate uses names and logic such as:

```text
Advanced ICMP: Unavailable by ICMP ping
Advanced ICMP: High packet loss
```

with availability based on:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#3)=0
```

and explicit dependencies on `Advanced ICMP: Collector error` to prevent collector failures from being reported as network outages.

## Recommended clean migration

### 1. Back up before changing links

Export the currently installed template and, for important environments, take the normal Zabbix/database backup used by your organization before clearing inherited entities.

### 2. Inspect the host before removing anything

Open:

```text
Data collection > Hosts > <host> > Triggers
```

and search for:

```text
advanced.ping
ICMP ping
```

Also review the linked templates for the host.

Current maintained triggers are prefixed with:

```text
Advanced ICMP:
```

Legacy triggers without this prefix should be reviewed before deletion. Do not remove similarly named triggers from unrelated templates without confirming their source.

### 3. If the legacy template is still linked

If you intentionally want to remove the old AdvancedPING entities, use **Unlink and clear** for the legacy template rather than plain **Unlink**.

Use this option only after confirming that the old entities are no longer required. If historical continuity is important, perform the migration on a test host first and follow your normal backup/change-control process before clearing production objects.

### 4. If the legacy template is already unlinked

If old entities were preserved by a previous **Unlink**, they may now be local host entities. Review them individually and remove only the confirmed legacy objects.

Useful identifiers include:

```text
advanced.ping.avg
advanced.ping.loss
advanced.ping.max
advanced.ping.min
advanced.ping.rcv
advanced.ping.xmt
advanced.ping.jitter
advanced.ping.stddev
advanced.ping.error
```

The presence of an `advanced.ping.*` key alone is not sufficient reason to delete an object, because the maintained template intentionally uses the same key namespace. Confirm whether the object is inherited from the current template or is a local legacy copy.

### 5. Link/import the maintained template

Import the export matching the installed Zabbix major version and link **Advanced ICMP Ping with Jitter** to the host.

Then verify that the host receives the expected maintained triggers:

```text
Advanced ICMP: Collector error
Advanced ICMP: High jitter
Advanced ICMP: High packet loss
Advanced ICMP: High response time
Advanced ICMP: High RTT standard deviation
Advanced ICMP: High time differences (Min/Max)
Advanced ICMP: Long unavailable by ICMP ping
Advanced ICMP: Unavailable by ICMP ping
```

## Post-upgrade validation

Validate at least the following scenarios on a test host before broad production rollout:

1. **Normal collection** — `xmt=20`, `rcv=20` or the expected received count, `error=""`;
2. **Collector configuration error** — only `Advanced ICMP: Collector error` should become a problem; network symptom triggers should remain suppressed by dependency;
3. **Recovery** — restoring a valid collector configuration should resolve the collector error automatically;
4. **Real unreachable target** — the collector should remain healthy (`error=""`), packets sent should reflect the configured probe count, packets received should be `0`, and the availability triggers should activate according to their configured windows;
5. **No duplicate legacy alerts** — no old `Unavailable by ICMP ping` / `High ICMP ping loss` events should coexist with the maintained `Advanced ICMP:` triggers unless another intentionally linked template provides them.

## Safer validation strategy

For major upgrades, the safest validation method is to create a temporary host linked **only** to the new template. This eliminates interference from unrelated templates and local legacy objects. Once the collector, items, triggers, dependencies, and recovery behavior are validated, migrate production hosts in a controlled way.
