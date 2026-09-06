#!/usr/bin/env python3
"""Validate versioned Zabbix exports and project-specific invariants."""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
VERSION_FILE = ROOT / "VERSION"
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
JITTER_TEMPLATE_FILE = "advanced-icmp-ping-with-jitter.yaml"
COLLECTOR_ERROR_TRIGGER = "Advanced ICMP: Collector error"
HIGH_PACKET_LOSS_TRIGGER = "Advanced ICMP: High packet loss"
EXPECTED_SCRIPT = "advanced_icmp_ping.py"
TEMPLATE_NAME = "Advanced ICMP Ping with Jitter"
AVAIL_KEY = "icmpping[,{$ADV_FPING_POOL_COUNT},{$ADV_FPING_INTERVAL_MS},,{$ADV_FPING_TIMEOUT_MS}]"
LOSS_KEY = (
    "icmppingloss[,{$ADV_FPING_POOL_COUNT},{$ADV_FPING_INTERVAL_MS},,{$ADV_FPING_TIMEOUT_MS}]"
)
AVG_KEY = (
    "icmppingsec[,{$ADV_FPING_POOL_COUNT},{$ADV_FPING_INTERVAL_MS},,{$ADV_FPING_TIMEOUT_MS},avg]"
)
STATS_INTERVAL_MACRO = "{$ADV_ICMP_STATS_INTERVAL}"
PROCESS_MARGIN_MS = 2000
MAX_PROCESS_RUNTIME_MS = 25000


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def normalize_tags(tags):
    return tuple(sorted((tag.get("tag", ""), str(tag.get("value", ""))) for tag in tags or []))


def normalize_preprocessing(steps):
    normalized = []
    for step in steps or []:
        normalized.append(
            (
                step.get("type", ""),
                tuple(str(value) for value in step.get("parameters", [])),
                str(step.get("error_handler", "")),
                str(step.get("error_handler_params", "")),
            )
        )
    return tuple(normalized)


def load_exports(filename):
    exports = {}
    for version_dir in sorted(TEMPLATES_DIR.glob("zabbix-*")):
        if not version_dir.is_dir():
            continue
        expected_version = version_dir.name.removeprefix("zabbix-")
        path = version_dir / filename
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        raw = path.read_text(encoding="utf-8")
        if "{${" in raw:
            fail(f"{path.relative_to(ROOT)} contains malformed Zabbix user macro syntax")
        if re.search(r"(^|\s)[&*]id[0-9]+", raw):
            fail(f"{path.relative_to(ROOT)} must not contain YAML aliases/anchors")
        data = yaml.safe_load(raw)
        try:
            export_version = str(data["zabbix_export"]["version"])
        except (KeyError, TypeError):
            fail(f"missing zabbix_export.version in {path.relative_to(ROOT)}")
        if export_version != expected_version:
            fail(
                f"{path.relative_to(ROOT)} declares Zabbix {export_version}, "
                f"but directory expects {expected_version}"
            )
        exports[expected_version] = (path, data)
    if not exports:
        fail(f"no versioned templates found for {filename}")
    return exports


def get_template(data):
    try:
        templates = data["zabbix_export"]["templates"]
        if len(templates) != 1:
            fail(f"expected one template per export, found {len(templates)}")
        return templates[0]
    except (KeyError, TypeError):
        fail("missing template data in export")


def collect_trigger_nodes(node):
    triggers = {}
    if isinstance(node, dict):
        if {"uuid", "name", "expression"}.issubset(node):
            dependencies = tuple(
                sorted(
                    (dependency.get("name", ""), str(dependency.get("expression", "")))
                    for dependency in node.get("dependencies", [])
                )
            )
            triggers[node["uuid"]] = {
                "name": node["name"],
                "expression": str(node["expression"]),
                "priority": str(node.get("priority", "NOT_CLASSIFIED")),
                "status": str(node.get("status", "ENABLED")),
                "dependencies": dependencies,
                "tags": normalize_tags(node.get("tags", [])),
            }
        for value in node.values():
            triggers.update(collect_trigger_nodes(value))
    elif isinstance(node, list):
        for value in node:
            triggers.update(collect_trigger_nodes(value))
    return triggers


def normalize_item(item):
    value_type = str(item.get("value_type", "UNSIGNED"))
    trends = item.get("trends")
    if trends is None and value_type in {"TEXT", "CHAR", "LOG"}:
        trends = "0"
    master_item = item.get("master_item", {})
    return {
        "uuid": item.get("uuid"),
        "type": str(item.get("type", "ZABBIX_PASSIVE")),
        "value_type": value_type,
        "units": str(item.get("units", "")),
        "history": str(item.get("history", "")),
        "trends": str(trends if trends is not None else ""),
        "status": str(item.get("status", "ENABLED")),
        "timeout": str(item.get("timeout", "")),
        "preprocessing": normalize_preprocessing(item.get("preprocessing", [])),
        "master_item": str(master_item.get("key", "")),
        "tags": normalize_tags(item.get("tags", [])),
    }


def normalize_dashboard(dashboard):
    widgets = []
    for page in dashboard.get("pages", []):
        for widget in page.get("widgets", []):
            fields = []
            for field in widget.get("fields", []):
                value = field.get("value", "")
                if isinstance(value, dict):
                    value = tuple(sorted((str(key), str(item)) for key, item in value.items()))
                else:
                    value = str(value)
                fields.append((str(field.get("type", "")), str(field.get("name", "")), value))
            widgets.append(
                (
                    str(widget.get("type", "")),
                    str(widget.get("width", "")),
                    str(widget.get("height", "")),
                    tuple(fields),
                )
            )
    return {"uuid": dashboard.get("uuid"), "widgets": tuple(widgets)}


def normalize_graph(graph):
    items = []
    for graph_item in graph.get("graph_items", []):
        item = graph_item.get("item", {})
        items.append(
            (
                str(graph_item.get("sortorder", "0")),
                str(graph_item.get("drawtype", "LINE")),
                str(graph_item.get("color", "")),
                str(graph_item.get("yaxisside", "LEFT")),
                str(graph_item.get("calc_fnc", "AVG")),
                str(item.get("key", "")),
            )
        )
    return {"uuid": graph.get("uuid"), "items": tuple(items)}


def template_signature(data):
    template = get_template(data)
    vendor = template.get("vendor", {})
    items = {item["key"]: normalize_item(item) for item in template.get("items", [])}
    macros = {macro["macro"]: str(macro.get("value", "")) for macro in template.get("macros", [])}
    dashboards = {
        dashboard["name"]: normalize_dashboard(dashboard)
        for dashboard in template.get("dashboards", [])
    }
    graphs = {
        graph["name"]: normalize_graph(graph) for graph in data["zabbix_export"].get("graphs", [])
    }
    return {
        "uuid": template.get("uuid"),
        "template": template.get("template"),
        "name": template.get("name"),
        "vendor_name": vendor.get("name"),
        "vendor_version": str(vendor.get("version", "")),
        "items": items,
        "macros": macros,
        "triggers": collect_trigger_nodes(data),
        "dashboards": dashboards,
        "graphs": graphs,
    }


def validate_version_file(exports):
    project_version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER_RE.fullmatch(project_version):
        fail(f"VERSION must use Semantic Versioning MAJOR.MINOR.PATCH, got {project_version!r}")
    for zabbix_version, (_, data) in exports.items():
        vendor_version = template_signature(data)["vendor_version"]
        if vendor_version != project_version:
            fail(
                f"Zabbix {zabbix_version} vendor.version is {vendor_version!r}, "
                f"but VERSION is {project_version!r}"
            )
    return project_version


def validate_cross_version_parity(exports):
    versions = sorted(exports)
    baseline_version = versions[0]
    baseline = template_signature(exports[baseline_version][1])
    invariant_fields = (
        "uuid",
        "template",
        "name",
        "vendor_name",
        "vendor_version",
        "items",
        "macros",
        "triggers",
        "dashboards",
        "graphs",
    )
    for version in versions[1:]:
        candidate = template_signature(exports[version][1])
        for field in invariant_fields:
            if candidate[field] != baseline[field]:
                fail(
                    f"cross-version mismatch in {field!r}: "
                    f"Zabbix {baseline_version} != Zabbix {version}"
                )


def validate_external_script(exports):
    for version, (_, data) in exports.items():
        template = get_template(data)
        external_items = [
            item for item in template.get("items", []) if item.get("type") == "EXTERNAL"
        ]
        if len(external_items) != 1:
            fail(f"Zabbix {version}: expected exactly one EXTERNAL master item")
        item = external_items[0]
        key = str(item.get("key", ""))
        if not key.startswith(f"{EXPECTED_SCRIPT}["):
            fail(f"Zabbix {version}: unexpected external item key {key!r}")
        if str(item.get("history", "")) != "1h":
            fail(f"Zabbix {version}: raw master item history must be 1h")
        if str(item.get("timeout", "")) != "30s":
            fail(f"Zabbix {version}: external master item timeout must remain 30s")
        if str(item.get("delay", "")) != STATS_INTERVAL_MACRO:
            fail(f"Zabbix {version}: external statistics item must use {STATS_INTERVAL_MACRO}")
        tags = set(normalize_tags(item.get("tags", [])))
        required = {("component", "network"), ("component", "raw")}
        if not required.issubset(tags):
            fail(f"Zabbix {version}: raw master item must have component network/raw tags")


def validate_macro_timing(exports):
    required = {"{$ADV_FPING_POOL_COUNT}", "{$ADV_FPING_INTERVAL_MS}", "{$ADV_FPING_TIMEOUT_MS}"}
    for version, (_, data) in exports.items():
        macros = {
            macro["macro"]: str(macro.get("value", ""))
            for macro in get_template(data).get("macros", [])
        }
        missing = required - set(macros)
        if missing:
            fail(f"Zabbix {version}: missing timing macros: {', '.join(sorted(missing))}")
        try:
            count = int(macros["{$ADV_FPING_POOL_COUNT}"])
            interval_ms = int(macros["{$ADV_FPING_INTERVAL_MS}"])
            timeout_ms = int(macros["{$ADV_FPING_TIMEOUT_MS}"])
        except ValueError:
            fail(f"Zabbix {version}: timing macro defaults must be integers")
        if timeout_ms > interval_ms:
            fail(
                f"Zabbix {version}: fping timeout ({timeout_ms}ms) must not exceed "
                f"period ({interval_ms}ms)"
            )
        estimated_runtime = count * interval_ms + timeout_ms + PROCESS_MARGIN_MS
        if estimated_runtime > MAX_PROCESS_RUNTIME_MS:
            fail(
                f"Zabbix {version}: default probe runtime {estimated_runtime}ms exceeds "
                f"collector budget {MAX_PROCESS_RUNTIME_MS}ms"
            )


def validate_collector_float_contract(exports):
    float_paths = {"$.avg", "$.jitter", "$.max", "$.min", "$.stddev", "$.loss"}
    for version, (_, data) in exports.items():
        for item in get_template(data).get("items", []):
            if item.get("type") != "DEPENDENT":
                continue
            jsonpaths = {
                str(value)
                for step in item.get("preprocessing", [])
                if step.get("type") == "JSONPATH"
                for value in step.get("parameters", [])
            }
            if jsonpaths & float_paths and str(item.get("value_type", "UNSIGNED")) != "FLOAT":
                fail(
                    f"Zabbix {version}: dependent item {item.get('key')!r} maps a float "
                    "collector field and must declare value_type FLOAT"
                )


def validate_item_tags(exports):
    for version, (_, data) in exports.items():
        for item in get_template(data).get("items", []):
            tags = normalize_tags(item.get("tags", []))
            if not any(name == "component" for name, _ in tags):
                fail(f"Zabbix {version}: item {item.get('key')!r} has no component tag")


def validate_trigger_policy(exports):
    required_names = {
        "Advanced ICMP: Collector error",
        "Advanced ICMP: High jitter",
        "Advanced ICMP: High packet loss",
        "Advanced ICMP: High response time",
        "Advanced ICMP: High RTT standard deviation",
        "Advanced ICMP: High time differences (Min/Max)",
        "Advanced ICMP: Long unavailable by ICMP ping",
        "Advanced ICMP: Unavailable by ICMP ping",
    }
    for version, (_, data) in exports.items():
        triggers = collect_trigger_nodes(data)
        names = {trigger["name"]: trigger for trigger in triggers.values()}
        if set(names) != required_names:
            fail(f"Zabbix {version}: hybrid trigger set differs from policy")

        short = names["Advanced ICMP: Unavailable by ICMP ping"]["expression"]
        long = names["Advanced ICMP: Long unavailable by ICMP ping"]["expression"]
        loss = names["Advanced ICMP: High packet loss"]["expression"]
        response = names["Advanced ICMP: High response time"]["expression"]

        if not all(
            token in short
            for token in (
                f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)=3",
                f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)<30",
                f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)>0",
            )
        ):
            fail(f"Zabbix {version}: short outage trigger must cover samples 3 through 29")
        if not all(
            token in long
            for token in (
                f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)=30",
                f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)=0",
            )
        ):
            fail(f"Zabbix {version}: long outage trigger must require 30 zero samples")
        if not all(
            token in loss
            for token in (
                f"min(/{TEMPLATE_NAME}/{LOSS_KEY},#2)",
                f"max(/{TEMPLATE_NAME}/{LOSS_KEY},#2)<100",
            )
        ):
            f"Zabbix {version}: packet loss trigger must use two degraded "
            "non-total-loss samples"
        if (
            f"avg(/{TEMPLATE_NAME}/{AVG_KEY},5m)" not in response
            or f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0" not in response
        ):
            fail(f"Zabbix {version}: response-time trigger must use native RTT and availability")

        advanced_names = {
            "Advanced ICMP: High jitter",
            "Advanced ICMP: High RTT standard deviation",
            "Advanced ICMP: High time differences (Min/Max)",
        }
        for name in advanced_names:
            trigger = names[name]
            dependency_names = {dependency for dependency, _ in trigger["dependencies"]}
            if {COLLECTOR_ERROR_TRIGGER, HIGH_PACKET_LOSS_TRIGGER} - dependency_names:
                f"Zabbix {version}: advanced trigger {name!r} must depend on "
                "collector error and packet loss"
            if f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0" not in trigger["expression"]:
                fail(
                    f"Zabbix {version}: advanced trigger {name!r} must recover during total outage"
                )

        core_names = {
            "Advanced ICMP: High packet loss",
            "Advanced ICMP: High response time",
            "Advanced ICMP: Long unavailable by ICMP ping",
            "Advanced ICMP: Unavailable by ICMP ping",
        }
        for name in core_names:
            dependency_names = {dependency for dependency, _ in names[name]["dependencies"]}
            if COLLECTOR_ERROR_TRIGGER in dependency_names:
                f"Zabbix {version}: native core trigger {name!r} must not depend "
                "on the external collector"

        for trigger in triggers.values():
            if trigger["priority"] == "DISASTER":
                fail(f"Zabbix {version}: resource template must not use DISASTER severity")
            if not any(name == "scope" for name, _ in trigger["tags"]):
                fail(f"Zabbix {version}: trigger {trigger['name']!r} has no scope tag")


def validate_hybrid_template(exports):
    expected_keys = {
        AVAIL_KEY,
        LOSS_KEY,
        AVG_KEY,
        "advanced.ping.error",
        "advanced.ping.jitter",
        "advanced.ping.max",
        "advanced.ping.min",
        "advanced.ping.stddev",
    }
    required_macros = {
        "{$ADV_FPING_POOL_COUNT}": "20",
        "{$ADV_FPING_INTERVAL_MS}": "250",
        "{$ADV_FPING_TIMEOUT_MS}": "250",
        STATS_INTERVAL_MACRO: "5m",
        "{$ADV_ICMP_LOSS_WARN}": "20",
        "{$ADV_ICMP_RESPONSE_TIME_WARN}": "200",
    }
    forbidden_legacy_keys = {
        "advanced.ping.avg",
        "advanced.ping.loss",
        "advanced.ping.rcv",
        "advanced.ping.xmt",
    }

    for version, (_, data) in exports.items():
        template = get_template(data)
        if template.get("template") != TEMPLATE_NAME:
            fail(f"Zabbix {version}: unexpected template name")

        items = template.get("items", [])
        items_by_key = {str(item.get("key", "")): item for item in items}
        external = [item for item in items if item.get("type") == "EXTERNAL"]
        if len(external) != 1:
            fail(f"Zabbix {version}: hybrid template must contain one advanced EXTERNAL item")
        if set(items_by_key) != expected_keys | {str(external[0].get("key", ""))}:
            fail(f"Zabbix {version}: hybrid item set differs from policy")
        if forbidden_legacy_keys & set(items_by_key):
            fail(f"Zabbix {version}: duplicate collector-derived core metrics are not allowed")

        for key in (AVAIL_KEY, LOSS_KEY, AVG_KEY):
            item = items_by_key[key]
            if item.get("type") != "SIMPLE":
                fail(f"Zabbix {version}: native core item {key!r} must be SIMPLE")
            if str(item.get("delay", "")) != "1m":
                fail(f"Zabbix {version}: native core item {key!r} must run every 1m")
            if str(item.get("history", "")) != "30d":
                fail(f"Zabbix {version}: native core item {key!r} must retain 30d history")
        for key in (LOSS_KEY, AVG_KEY):
            if str(items_by_key[key].get("value_type", "UNSIGNED")) != "FLOAT":
                fail(f"Zabbix {version}: native metric {key!r} must be FLOAT")
        if ("MULTIPLIER", ("1000",), "", "") not in normalize_preprocessing(
            items_by_key[AVG_KEY].get("preprocessing", [])
        ):
            fail(f"Zabbix {version}: native RTT must convert seconds to milliseconds")

        master_key = str(external[0].get("key", ""))
        for key in (
            "advanced.ping.error",
            "advanced.ping.jitter",
            "advanced.ping.max",
            "advanced.ping.min",
            "advanced.ping.stddev",
        ):
            item = items_by_key[key]
            if item.get("type") != "DEPENDENT":
                fail(f"Zabbix {version}: advanced statistic {key!r} must be DEPENDENT")
            if str(item.get("master_item", {}).get("key", "")) != master_key:
                fail(f"Zabbix {version}: advanced statistic {key!r} has wrong master item")
            if str(item.get("history", "")) != "30d":
                fail(f"Zabbix {version}: advanced statistic {key!r} must retain 30d history")
        for key in (
            "advanced.ping.jitter",
            "advanced.ping.max",
            "advanced.ping.min",
            "advanced.ping.stddev",
        ):
            if str(items_by_key[key].get("value_type", "UNSIGNED")) != "FLOAT":
                fail(f"Zabbix {version}: advanced statistic {key!r} must be FLOAT")
        if str(items_by_key["advanced.ping.error"].get("value_type", "UNSIGNED")) != "TEXT":
            fail(f"Zabbix {version}: collector error must be TEXT")

        macros = {m["macro"]: str(m.get("value", "")) for m in template.get("macros", [])}
        for macro, expected in required_macros.items():
            if macros.get(macro) != expected:
                fail(f"Zabbix {version}: macro {macro} must default to {expected}")


def main():
    exports = load_exports(JITTER_TEMPLATE_FILE)
    for version_dir in sorted(TEMPLATES_DIR.glob("zabbix-*")):
        if (version_dir / "advanced-icmp-ping.yaml").exists():
            f"{version_dir.name}: separate native template must not exist; "
            "the project ships one hybrid template"

    project_version = validate_version_file(exports)
    validate_cross_version_parity(exports)
    validate_external_script(exports)
    validate_macro_timing(exports)
    validate_collector_float_contract(exports)
    validate_item_tags(exports)
    validate_hybrid_template(exports)
    validate_trigger_policy(exports)

    versions = ", ".join(sorted(exports))
    f"OK: single hybrid ICMP template validated for Zabbix {versions}; "
    f"project version {project_version}"


if __name__ == "__main__":
    main()
