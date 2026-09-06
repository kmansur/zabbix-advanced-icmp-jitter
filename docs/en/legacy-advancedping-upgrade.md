# Upgrading from legacy AdvancedPING

[English](legacy-advancedping-upgrade.md) | [Português (Brasil)](../pt-BR/legacy-advancedping-upgrade.md)

A plain **Unlink** can leave inherited AdvancedPING entities on a host as local objects. If the intention is to remove those inherited legacy objects too, use **Unlink and clear** only after reviewing the impact and following the normal backup/change-control process.

Before broad rollout, validate on a clean temporary host and look for duplicate legacy triggers such as `Unavailable by ICMP ping` or `High ICMP ping loss`. The maintained template uses the `Advanced ICMP:` trigger prefix.

Do not delete an object only because it uses an `advanced.ping.*` key; the maintained template uses the same namespace. Confirm the object's source first.
