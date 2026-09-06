#!/usr/bin/env python3
"""Validate Advanced ICMP Ping with Jitter exports and project invariants."""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = "advanced-icmp-ping-with-jitter.yaml"
TEMPLATE_NAME = "Advanced ICMP Ping with Jitter"
PROJECT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
FLOAT_KEYS = {
    "advanced.ping.avg",
    "advanced.ping.loss",
    "advanced.ping.max",
    "advanced.ping.min",
    "advanced.ping.jitter",
    "advanced.ping.stddev",
}
EXPECTED_KEYS = FLOAT_KEYS | {"advanced.ping.rcv", "advanced.ping.xmt", "advanced.ping.error"}
COLLECTOR_ERROR = "Advanced ICMP: Collector error"
COLLECTOR_DEPENDENCY_TARGETS = {
    "Advanced ICMP: High response time",
    "Advanced ICMP: High jitter",
    "Advanced ICMP: High packet loss",
    "Advanced ICMP: High RTT standard deviation",
    "Advanced ICMP: High time differences (Min/Max)",
    "Advanced ICMP: Long unavailable by ICMP ping",
    "Advanced ICMP: Unavailable by ICMP ping",
}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def collect_triggers(node):
    triggers = []
    if isinstance(node, dict):
        if {"name", "expression", "priority"}.issubset(node):
            triggers.append(node)
        for value in node.values():
            triggers.extend(collect_triggers(value))
    elif isinstance(node, list):
        for value in node:
            triggers.extend(collect_triggers(value))
    return triggers


def item_signature(item):
    preprocessing = tuple(
        (step.get("type", ""), tuple(str(v) for v in step.get("parameters", [])))
        for step in item.get("preprocessing", [])
    )
    return (
        item.get("name", ""),
        item.get("key", ""),
        item.get("type", ""),
        str(item.get("history", "")),
        item.get("value_type", ""),
        item.get("units", ""),
        preprocessing,
    )


def trigger_signature(trigger):
    deps = tuple(
        sorted(
            (dep.get("name", ""), str(dep.get("expression", "")))
            for dep in trigger.get("dependencies", [])
        )
    )
    return (
        trigger.get("name", ""),
        str(trigger.get("expression", "")),
        trigger.get("priority", ""),
        trigger.get("status", "ENABLED"),
        deps,
    )


def validate(version):
    path = ROOT / "templates" / f"zabbix-{version}" / TEMPLATE_FILE
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if str(data["zabbix_export"]["version"]) != version:
        fail(f"Zabbix {version}: export version mismatch")
    template = data["zabbix_export"]["templates"][0]
    if template.get("template") != TEMPLATE_NAME:
        fail(f"Zabbix {version}: template name mismatch")
    if str(template.get("vendor", {}).get("version", "")) != PROJECT_VERSION:
        fail(f"Zabbix {version}: vendor.version must match VERSION ({PROJECT_VERSION})")
    for item in template.get("items", []):
        key = str(item.get("key", ""))
        if key.startswith(("icmpping[", "icmppingloss[", "icmppingsec[")):
            fail(f"Zabbix {version}: native Zabbix ICMP keys are not allowed")
    items = {item["key"]: item for item in template.get("items", [])}
    if not EXPECTED_KEYS.issubset(items):
        fail(f"Zabbix {version}: missing expected dependent items")
    for key in FLOAT_KEYS:
        if items[key].get("value_type") != "FLOAT":
            fail(f"Zabbix {version}: {key} must explicitly use FLOAT")
    if items["advanced.ping.error"].get("value_type") != "TEXT":
        fail(f"Zabbix {version}: advanced.ping.error must be TEXT")
    masters = [
        item
        for item in template.get("items", [])
        if str(item.get("key", "")).startswith("advanced_icmp_ping.py[")
    ]
    if len(masters) != 1:
        fail(f"Zabbix {version}: exactly one external master is required")
    if masters[0].get("type") != "EXTERNAL" or masters[0].get("value_type") != "TEXT":
        fail(f"Zabbix {version}: master item must be EXTERNAL/TEXT")
    if str(masters[0].get("history", "")) != "1h":
        fail(f"Zabbix {version}: raw JSON history must be 1h")
    triggers = collect_triggers(data)
    by_name = {trigger["name"]: trigger for trigger in triggers}
    packet = by_name.get("Advanced ICMP: High packet loss")
    if packet is None:
        fail(f"Zabbix {version}: packet loss trigger missing")
    packet_expr = str(packet.get("expression", ""))
    if "min(/Advanced ICMP Ping with Jitter/advanced.ping.loss,#2)" not in packet_expr:
        fail(f"Zabbix {version}: packet loss must require two consecutive degraded samples")
    if "min(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#2)>0" not in packet_expr:
        fail(f"Zabbix {version}: packet loss must suppress total outages")
    if "last(/Advanced ICMP Ping with Jitter/advanced.ping.loss,#2)" in raw:
        fail(f"Zabbix {version}: obsolete last(loss,#2) expression found")
    for name in COLLECTOR_DEPENDENCY_TARGETS:
        trigger = by_name.get(name)
        if trigger is None:
            fail(f"Zabbix {version}: missing trigger {name!r}")
        deps = {dep.get("name") for dep in trigger.get("dependencies", [])}
        if COLLECTOR_ERROR not in deps:
            fail(f"Zabbix {version}: {name!r} must depend on Collector error")
    macros = tuple(
        sorted((m.get("macro", ""), str(m.get("value", ""))) for m in template.get("macros", []))
    )
    return (
        tuple(sorted(item_signature(item) for item in template.get("items", []))),
        tuple(sorted(trigger_signature(trigger) for trigger in triggers)),
        macros,
    )


def main():
    for path in (ROOT / "templates").glob("zabbix-*/advanced-icmp-ping.yaml"):
        if path.exists():
            fail("separate Advanced ICMP Ping template must not exist")
    signatures = {version: validate(version) for version in ("7.0", "8.0")}
    if signatures["7.0"] != signatures["8.0"]:
        fail("Zabbix 7.0 and 8.0 templates are not semantically equivalent")
    print(f"OK: approved non-hybrid templates validated; project version {PROJECT_VERSION}")


if __name__ == "__main__":
    main()
