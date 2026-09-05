#!/usr/bin/env python3
"""Validate versioned Zabbix template exports and cross-version invariants."""

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
VERSION_FILE = ROOT / "VERSION"


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


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


def collect_triggers(node):
    triggers = {}

    if isinstance(node, dict):
        if {"uuid", "name", "expression"}.issubset(node):
            triggers[node["uuid"]] = (node["name"], node["expression"])
        for value in node.values():
            triggers.update(collect_triggers(value))
    elif isinstance(node, list):
        for value in node:
            triggers.update(collect_triggers(value))

    return triggers


def template_signature(data):
    template = get_template(data)
    vendor = template.get("vendor", {})

    items = {item["key"]: item["uuid"] for item in template.get("items", [])}
    macros = {macro["macro"] for macro in template.get("macros", [])}
    dashboards = {
        dashboard["name"]: dashboard["uuid"] for dashboard in template.get("dashboards", [])
    }
    graphs = {
        graph["name"]: graph["uuid"] for graph in data["zabbix_export"].get("graphs", [])
    }

    return {
        "uuid": template.get("uuid"),
        "template": template.get("template"),
        "name": template.get("name"),
        "vendor_name": vendor.get("name"),
        "vendor_version": str(vendor.get("version", "")),
        "items": items,
        "macros": macros,
        "triggers": collect_triggers(data),
        "dashboards": dashboards,
        "graphs": graphs,
    }


def validate_version_file(exports):
    project_version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not project_version:
        fail("VERSION is empty")

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


def validate_external_script_reference(exports):
    expected_script = "advanced_icmp_ping.py"

    for version, (_, data) in exports.items():
        template = get_template(data)
        external_items = [item for item in template.get("items", []) if item.get("type") == "EXTERNAL"]
        if len(external_items) != 1:
            fail(f"Zabbix {version}: expected exactly one EXTERNAL item")

        key = external_items[0].get("key", "")
        if not key.startswith(f"{expected_script}["):
            fail(f"Zabbix {version}: unexpected external item key {key!r}")


def main():
    exports = load_exports()
    project_version = validate_version_file(exports)
    validate_cross_version_parity(exports)
    validate_external_script_reference(exports)

    versions = ", ".join(sorted(exports))
    print(f"OK: templates validated for Zabbix {versions}; project version {project_version}")


if __name__ == "__main__":
    main()
