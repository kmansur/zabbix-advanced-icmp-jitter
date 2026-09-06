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
COLLECTOR_ERROR_TRIGGER = "Advanced ICMP: Collector error"
HIGH_PACKET_LOSS_TRIGGER = "Advanced ICMP: High packet loss"
EXPECTED_SCRIPT = "advanced_icmp_ping.py"
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


def load_exports():
    exports = {}

    for version_dir in sorted(TEMPLATES_DIR.glob("zabbix-*")):
        if not version_dir.is_dir():
            continue

        expected_version = version_dir.name.removeprefix("zabbix-")
        yaml_files = sorted(version_dir.glob("*.yaml"))
        if not yaml_files:
            fail(f"no YAML template found in {version_dir.relative_to(ROOT)}")
        if len(yaml_files) != 1:
            fail(
                f"expected exactly one YAML template in {version_dir.relative_to(ROOT)}, "
                f"found {len(yaml_files)}"
            )

        path = yaml_files[0]
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

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
        fail("no versioned templates found")

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

        tags = set(normalize_tags(item.get("tags", [])))
        required = {("component", "network"), ("component", "raw")}
        if not required.issubset(tags):
            fail(f"Zabbix {version}: raw master item must have component network/raw tags")


def validate_macro_timing(exports):
    required = {
        "{$ADV_FPING_POOL_COUNT}",
        "{$ADV_FPING_INTERVAL_MS}",
        "{$ADV_FPING_TIMEOUT_MS}",
    }

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


def validate_item_tags(exports):
    for version, (_, data) in exports.items():
        for item in get_template(data).get("items", []):
            tags = normalize_tags(item.get("tags", []))
            if not any(name == "component" for name, _ in tags):
                fail(f"Zabbix {version}: item {item.get('key')!r} has no component tag")


def validate_trigger_policy(exports):
    for version, (_, data) in exports.items():
        triggers = collect_trigger_nodes(data)
        if not triggers:
            fail(f"Zabbix {version}: no triggers found")

        names = {trigger["name"]: trigger for trigger in triggers.values()}
        packet_loss = names.get(HIGH_PACKET_LOSS_TRIGGER)
        if packet_loss is None:
            fail(f"Zabbix {version}: high packet loss trigger not found")
        if (
            "min(/Advanced ICMP Ping with Jitter/advanced.ping.loss,#2)"
            not in packet_loss["expression"]
        ):
            fail(f"Zabbix {version}: packet loss trigger must evaluate both latest samples")

        for trigger in triggers.values():
            if (
                "last(/Advanced ICMP Ping with Jitter/advanced.ping.loss,#2)"
                in trigger["expression"]
            ):
                fail(f"Zabbix {version}: trigger {trigger['name']!r} uses last(...,#2) incorrectly")

            for _, expression in trigger["dependencies"]:
                if "last(/Advanced ICMP Ping with Jitter/advanced.ping.loss,#2)" in expression:
                    fail(
                        f"Zabbix {version}: dependency of {trigger['name']!r} "
                        "uses last(...,#2) incorrectly"
                    )

            if trigger["priority"] == "DISASTER":
                fail(f"Zabbix {version}: resource template must not use DISASTER severity")

            if not any(name == "scope" for name, _ in trigger["tags"]):
                fail(f"Zabbix {version}: trigger {trigger['name']!r} has no scope tag")

            if trigger["name"] != COLLECTOR_ERROR_TRIGGER:
                dependency_names = {name for name, _ in trigger["dependencies"]}
                if COLLECTOR_ERROR_TRIGGER not in dependency_names:
                    fail(
                        f"Zabbix {version}: trigger {trigger['name']!r} must depend on "
                        f"{COLLECTOR_ERROR_TRIGGER!r}"
                    )


def main():
    exports = load_exports()
    project_version = validate_version_file(exports)
    validate_cross_version_parity(exports)
    validate_external_script(exports)
    validate_macro_timing(exports)
    validate_item_tags(exports)
    validate_trigger_policy(exports)

    versions = ", ".join(sorted(exports))
    print(f"OK: templates validated for Zabbix {versions}; project version {project_version}")


if __name__ == "__main__":
    main()
