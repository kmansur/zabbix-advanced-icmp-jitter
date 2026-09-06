# Zabbix 8.0 compatibility

[English](zabbix-8.0.md) | [Português (Brasil)](../pt-BR/zabbix-8.0.md)

The project provides a dedicated Zabbix 8.0 export at:

```text
templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml
```

This file was produced from a template successfully imported into **Zabbix 8.0 Beta 2** and then exported again by the Zabbix frontend.

> **Compatibility status:** tested and validated on Zabbix 8.0 Beta 2. This documentation and export will be reviewed and updated as new Beta, RC, and final Zabbix 8.0 builds are tested.

## Validation

The 8.0 version was compared with the project's Zabbix 7.0 template. Monitoring logic was preserved:

- same template UUID and name;
- same vendor and template version (`Net Tech`, `1.0-10`);
- same 10 items and keys;
- same 8 macros and default values;
- same trigger expressions and dependencies;
- same dashboard;
- same graph and series;
- same external script `advanced_icmp_ping.py`.

Observed differences are Zabbix 8.0 export serialization differences and do not change template logic. They include:

- `zabbix_export.version` changes from `7.0` to `8.0`;
- some default-valued fields are no longer exported explicitly;
- item and macro ordering may be normalized by Zabbix;
- the dashboard explicitly records `auto_start: 'YES'`;
- the graph retains the upper limit of `200`, while some default axis values are no longer explicitly present in YAML.

## Import

In the Zabbix 8.0 frontend:

1. open **Data collection > Templates**;
2. click **Import**;
3. select `templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml`;
4. review the changes shown by the frontend;
5. complete the import;
6. link the template to the required hosts.

The Python collector is the same one used by the 7.0 version and must be installed in the Zabbix Server or Proxy `ExternalScripts` directory.

## 8.0 compatibility update policy

While Zabbix 8.0 is still evolving, `templates/zabbix-8.0/` represents the most recent build effectively tested by the project.

After each relevant validation (Beta, RC, or final release), the documentation must explicitly record the tested version. If a newer Zabbix build changes the export format or requires template adjustments, the YAML will be updated from a newly validated export.

## Official reference

The official Zabbix 8.0 documentation defines `zabbix_export.version: '8.0'` for YAML exports and supports templates containing dependent items, preprocessing, triggers, dashboards, and graphs. The maintained export follows that structure.
