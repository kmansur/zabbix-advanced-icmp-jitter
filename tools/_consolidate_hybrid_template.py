#!/usr/bin/env python3
"""One-shot consolidation of the native ICMP core and advanced jitter collector."""

from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_NAME = "Advanced ICMP Ping with Jitter"
TEMPLATE_UUID = "afac17c2c17e443cbf0af2ae2963bede"
VALUE_MAP_UUID = "4778ae245e7a49a1821649965afc9a91"

AVAIL_UUID = "1670e4d8e9054effa23a6b598e325caa"
AVG_UUID = "b483670491814d98b37dff153750a40e"
LOSS_UUID = "eb3e547aeda94ba999b0e84f78c9bfb7"
MAX_UUID = "982689cec232435fb57158b5f617ca3f"
MIN_UUID = "2c67d51b3fb64d2288bf6dd7ad6d55d7"
JITTER_UUID = "7bcb6943d5eb46b692dcf31e88fa3938"
STDDEV_UUID = "9d983174608b4f3db4d0960aff79ed6d"
ERROR_UUID = "27e61fa62b8c405da36588bd5c24b379"
RAW_UUID = "d9869868444741b89cdca6911682582b"

LONG_UUID = "e80be54fd2174e84b64ec3a9261864d9"
SHORT_UUID = "060dd4f74b0a4f83aa75b27623050c0a"
RESPONSE_UUID = "f751fa9758054945915c723f0239f4e2"
LOSS_TRIGGER_UUID = "bb58843328ad49e6a9ac912dc5941998"
JITTER_TRIGGER_UUID = "9a9d437b891c4763a44dfe3f9505e7da"
STDDEV_TRIGGER_UUID = "80d9bf40f49a4fdf917c9371b0cfb0e3"
ERROR_TRIGGER_UUID = "433ce45731234c51aa71cb0e2f9d3a38"
MINMAX_TRIGGER_UUID = "78a9e6a9e9d34128b659e18871d6e3d1"

COUNT = "{$ADV_FPING_POOL_COUNT}"
INTERVAL = "{$ADV_FPING_INTERVAL_MS}"
TIMEOUT = "{$ADV_FPING_TIMEOUT_MS}"
STATS_INTERVAL = "{$ADV_ICMP_STATS_INTERVAL}"
AVAIL_KEY = f"icmpping[,{COUNT},{INTERVAL},,{TIMEOUT}]"
LOSS_KEY = f"icmppingloss[,{COUNT},{INTERVAL},,{TIMEOUT}]"
AVG_KEY = f"icmppingsec[,{COUNT},{INTERVAL},,{TIMEOUT},avg]"
RAW_KEY = f'advanced_icmp_ping.py["{{HOST.CONN}}","{COUNT}","{INTERVAL}","{TIMEOUT}"]'


def tags(*pairs):
    return [{"tag": key, "value": value} for key, value in pairs]


def dep(name, expression):
    return {"name": name, "expression": expression}


def trigger(uuid, name, expression, priority, scope, *, status=None, dependencies=None, description=None):
    result = {
        "uuid": uuid,
        "expression": expression,
        "name": name,
        "priority": priority,
    }
    if status:
        result["status"] = status
    if description:
        result["description"] = description
    if dependencies:
        result["dependencies"] = dependencies
    result["tags"] = tags(*[("scope", value) for value in scope])
    return result


def dependent_item(version, uuid, name, key, jsonpath, *, value_type="FLOAT", units="ms", description=None, item_triggers=None, extra_tags=None):
    item = {
        "uuid": uuid,
        "name": name,
        "type": "DEPENDENT",
        "key": key,
    }
    if version == "7.0":
        item["delay"] = "0"
    item["history"] = "30d"
    item["value_type"] = value_type
    if value_type in {"TEXT", "CHAR", "LOG"} and version == "7.0":
        item["trends"] = "0"
    if units:
        item["units"] = units
    if description:
        item["description"] = description
    item["preprocessing"] = [{"type": "JSONPATH", "parameters": [jsonpath]}]
    item["master_item"] = {"key": RAW_KEY}
    component_tags = [("component", "network")]
    if extra_tags:
        component_tags.extend(extra_tags)
    item["tags"] = tags(*component_tags)
    if item_triggers:
        item["triggers"] = item_triggers
    return item


def transform_template(version):
    path = ROOT / f"templates/zabbix-{version}/advanced-icmp-ping-with-jitter.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    template = data["zabbix_export"]["templates"][0]
    if template.get("uuid") != TEMPLATE_UUID:
        raise SystemExit(f"{path}: unexpected template UUID")

    short_expr = (
        f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)=3 and "
        f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)=0 and "
        f"(count(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)<30 or "
        f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)>0)"
    )
    long_expr = (
        f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)=30 and "
        f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)=0"
    )
    loss_expr = (
        f"min(/{TEMPLATE_NAME}/{LOSS_KEY},#2)>{{${{ADV_ICMP_LOSS_WARN}}}} and "
        f"max(/{TEMPLATE_NAME}/{LOSS_KEY},#2)<100"
    )
    response_expr = (
        f"avg(/{TEMPLATE_NAME}/{AVG_KEY},5m)>{{${{ADV_ICMP_RESPONSE_TIME_WARN}}}} and "
        f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0"
    )
    error_expr = f'last(/{TEMPLATE_NAME}/advanced.ping.error)<>""'
    jitter_expr = (
        f"avg(/{TEMPLATE_NAME}/advanced.ping.jitter,10m)>{{${{ADV_ICMP_JITTER_WARN}}}} and "
        f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0"
    )
    stddev_expr = (
        f"avg(/{TEMPLATE_NAME}/advanced.ping.stddev,10m)>{{${{ADV_ICMP_STDDEV_WARN}}}} and "
        f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0"
    )
    minmax_expr = (
        f"avg(/{TEMPLATE_NAME}/advanced.ping.min,10m)>0 and "
        f"avg(/{TEMPLATE_NAME}/advanced.ping.max,10m)/"
        f"avg(/{TEMPLATE_NAME}/advanced.ping.min,10m)>{{${{ADV_ICMP_MAX_TIME_MULTIPLE}}}} and "
        f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0"
    )

    long_trigger = trigger(
        LONG_UUID,
        "Advanced ICMP: Long unavailable by ICMP ping",
        long_expr,
        "HIGH",
        ["availability"],
        description="Thirty consecutive one-minute native ICMP batches failed (approximately 30 minutes).",
    )
    short_trigger = trigger(
        SHORT_UUID,
        "Advanced ICMP: Unavailable by ICMP ping",
        short_expr,
        "AVERAGE",
        ["availability"],
        description="Three consecutive one-minute native ICMP batches failed. This event is mutually exclusive with the long outage event.",
    )
    high_loss_trigger = trigger(
        LOSS_TRIGGER_UUID,
        "Advanced ICMP: High packet loss",
        loss_expr,
        "WARNING",
        ["availability", "performance"],
        description="Packet loss stayed above the threshold for two native ICMP batches. Total loss is handled by availability triggers.",
    )
    high_response_trigger = trigger(
        RESPONSE_UUID,
        "Advanced ICMP: High response time",
        response_expr,
        "WARNING",
        ["performance"],
        dependencies=[dep("Advanced ICMP: High packet loss", loss_expr)],
    )
    collector_trigger = trigger(
        ERROR_TRIGGER_UUID,
        "Advanced ICMP: Collector error",
        error_expr,
        "WARNING",
        ["availability"],
        description="The optional advanced statistics collector failed. Native availability, loss and average RTT continue independently.",
    )
    advanced_dependencies = [
        dep("Advanced ICMP: High packet loss", loss_expr),
        dep("Advanced ICMP: Collector error", error_expr),
    ]
    high_jitter_trigger = trigger(
        JITTER_TRIGGER_UUID,
        "Advanced ICMP: High jitter",
        jitter_expr,
        "WARNING",
        ["performance"],
        dependencies=advanced_dependencies,
    )
    high_stddev_trigger = trigger(
        STDDEV_TRIGGER_UUID,
        "Advanced ICMP: High RTT standard deviation",
        stddev_expr,
        "WARNING",
        ["performance"],
        status="DISABLED",
        dependencies=advanced_dependencies,
    )
    minmax_trigger = trigger(
        MINMAX_TRIGGER_UUID,
        "Advanced ICMP: High time differences (Min/Max)",
        minmax_expr,
        "WARNING",
        ["performance"],
        dependencies=advanced_dependencies,
    )

    availability = {
        "uuid": AVAIL_UUID,
        "name": "Advanced ICMP: availability",
        "type": "SIMPLE",
        "key": AVAIL_KEY,
        "delay": "1m",
        "history": "30d",
        "description": "Native Zabbix ICMP availability. Returns 1 when at least one probe replies and 0 on total loss.",
        "valuemap": {"name": "Advanced ICMP service state"},
        "tags": tags(("component", "health"), ("component", "network")),
        "triggers": [long_trigger, short_trigger],
    }
    average = {
        "uuid": AVG_UUID,
        "name": "Advanced ICMP: average response time",
        "type": "SIMPLE",
        "key": AVG_KEY,
        "delay": "1m",
        "history": "30d",
        "value_type": "FLOAT",
        "units": "ms",
        "description": "Average RTT from the native Zabbix ICMP pinger, converted from seconds to milliseconds.",
        "preprocessing": [{"type": "MULTIPLIER", "parameters": ["1000"]}],
        "tags": tags(("component", "network"), ("component", "performance")),
        "triggers": [high_response_trigger],
    }
    packet_loss = {
        "uuid": LOSS_UUID,
        "name": "Advanced ICMP: packet loss",
        "type": "SIMPLE",
        "key": LOSS_KEY,
        "delay": "1m",
        "history": "30d",
        "value_type": "FLOAT",
        "units": "%",
        "description": "Packet loss percentage from the native Zabbix ICMP pinger.",
        "tags": tags(("component", "health"), ("component", "network")),
        "triggers": [high_loss_trigger],
    }

    jitter = dependent_item(
        version,
        JITTER_UUID,
        "Advanced ICMP: jitter",
        "advanced.ping.jitter",
        "$.jitter",
        description="Packet-to-packet jitter calculated from the individual RTT samples collected by the advanced statistics probe.",
        item_triggers=[high_jitter_trigger],
        extra_tags=[("component", "performance")],
    )
    stddev = dependent_item(
        version,
        STDDEV_UUID,
        "Advanced ICMP: RTT standard deviation",
        "advanced.ping.stddev",
        "$.stddev",
        description="Population standard deviation of RTT samples from the same advanced probe batch.",
        item_triggers=[high_stddev_trigger],
        extra_tags=[("component", "performance")],
    )
    minimum = dependent_item(
        version,
        MIN_UUID,
        "Advanced ICMP: minimum response time",
        "advanced.ping.min",
        "$.min",
        description="Minimum RTT from the same advanced statistics packet batch.",
        extra_tags=[("component", "performance")],
    )
    maximum = dependent_item(
        version,
        MAX_UUID,
        "Advanced ICMP: maximum response time",
        "advanced.ping.max",
        "$.max",
        description="Maximum RTT from the same advanced statistics packet batch.",
        extra_tags=[("component", "performance")],
    )
    collector_error = dependent_item(
        version,
        ERROR_UUID,
        "Advanced ICMP: collector error",
        "advanced.ping.error",
        "$.error",
        value_type="TEXT",
        units=None,
        description="Error returned only by the advanced statistics collector. Native ICMP checks are independent of this item.",
        item_triggers=[collector_trigger],
        extra_tags=[("component", "system")],
    )
    raw = {
        "uuid": RAW_UUID,
        "name": "Advanced ICMP: advanced statistics raw JSON",
        "type": "EXTERNAL",
        "key": RAW_KEY,
        "delay": STATS_INTERVAL,
        "history": "1h",
        "value_type": "TEXT",
    }
    if version == "7.0":
        raw["trends"] = "0"
    raw["timeout"] = "30s"
    raw["description"] = "Lower-frequency external probe used only for jitter, RTT deviation and same-batch min/max statistics."
    raw["tags"] = tags(("component", "network"), ("component", "raw"))

    template["description"] = (
        "Single hybrid ICMP template based on AdvancedPING by Dusan Priechodsky.\n\n"
        "The high-frequency monitoring path uses the native Zabbix ICMP pinger for availability, packet loss and average RTT, enabling target batching and good scale. "
        "A lower-frequency external Python/fping probe is retained only for packet-level jitter, RTT standard deviation and min/max from the same packet batch.\n\n"
        "Original project: https://github.com/priechodsky/AdvancedPING\n"
        "Modified by Karim Mansur / Net Tech.\n"
        "License: GNU General Public License v3.0 (GPL-3.0)."
    )
    template["items"] = [
        availability,
        average,
        packet_loss,
        jitter,
        stddev,
        minimum,
        maximum,
        collector_error,
        raw,
    ]
    template["tags"] = tags(("class", "network"), ("target", "icmp"))
    template["macros"] = [
        {
            "macro": COUNT,
            "value": "20",
            "description": "Number of probes used by both the native ICMP core and the advanced statistics batch.",
        },
        {
            "macro": INTERVAL,
            "value": "250",
            "description": "Period between probes in milliseconds for native and advanced measurements.",
        },
        {
            "macro": TIMEOUT,
            "value": "250",
            "description": "Per-probe timeout in milliseconds. Keep it less than or equal to the probe interval.",
        },
        {
            "macro": STATS_INTERVAL,
            "value": "5m",
            "description": "Update interval of the external jitter/stddev collector. Native availability, loss and average RTT remain at 1m.",
        },
        {"macro": "{$ADV_ICMP_LOSS_WARN}", "value": "20", "description": "Packet loss warning threshold in percent."},
        {"macro": "{$ADV_ICMP_JITTER_WARN}", "value": "20", "description": "Packet-level jitter warning threshold in milliseconds."},
        {"macro": "{$ADV_ICMP_MAX_TIME_MULTIPLE}", "value": "30", "description": "Maximum allowed ratio between same-batch max and min RTT."},
        {"macro": "{$ADV_ICMP_RESPONSE_TIME_WARN}", "value": "200", "description": "Average RTT warning threshold in milliseconds."},
        {"macro": "{$ADV_ICMP_STDDEV_WARN}", "value": "30", "description": "RTT standard deviation warning threshold in milliseconds. Trigger disabled by default."},
    ]
    template["valuemaps"] = [
        {
            "uuid": VALUE_MAP_UUID,
            "name": "Advanced ICMP service state",
            "mappings": [
                {"value": "0", "newvalue": "Down"},
                {"value": "1", "newvalue": "Up"},
            ],
        }
    ]

    data["zabbix_export"]["triggers"] = [minmax_trigger]
    for graph in data["zabbix_export"].get("graphs", []):
        for graph_item in graph.get("graph_items", []):
            item = graph_item.get("item", {})
            if item.get("key") == "advanced.ping.loss":
                item["key"] = LOSS_KEY
            elif item.get("key") == "advanced.ping.avg":
                item["key"] = AVG_KEY

    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")


for version in ("7.0", "8.0"):
    transform_template(version)
    native = ROOT / f"templates/zabbix-{version}/advanced-icmp-ping.yaml"
    if native.exists():
        native.unlink()

validator_path = ROOT / "tools/validate_templates.py"
validator = validator_path.read_text(encoding="utf-8")
validator = validator.replace('NATIVE_TEMPLATE_FILE = "advanced-icmp-ping.yaml"\n', "")
validator = validator.replace(
    'EXPECTED_SCRIPT = "advanced_icmp_ping.py"\n',
    'EXPECTED_SCRIPT = "advanced_icmp_ping.py"\n'
    'TEMPLATE_NAME = "Advanced ICMP Ping with Jitter"\n'
    'AVAIL_KEY = "icmpping[,{$ADV_FPING_POOL_COUNT},{$ADV_FPING_INTERVAL_MS},,{$ADV_FPING_TIMEOUT_MS}]"\n'
    'LOSS_KEY = "icmppingloss[,{$ADV_FPING_POOL_COUNT},{$ADV_FPING_INTERVAL_MS},,{$ADV_FPING_TIMEOUT_MS}]"\n'
    'AVG_KEY = "icmppingsec[,{$ADV_FPING_POOL_COUNT},{$ADV_FPING_INTERVAL_MS},,{$ADV_FPING_TIMEOUT_MS},avg]"\n'
    'STATS_INTERVAL_MACRO = "{$ADV_ICMP_STATS_INTERVAL}"\n',
)
validator = validator.replace(
    '        if str(item.get("delay", "")) != "1m":\n            fail(f"Zabbix {version}: external master item update interval must remain 1m")\n',
    '        if str(item.get("delay", "")) != STATS_INTERVAL_MACRO:\n'
    '            fail(f"Zabbix {version}: external statistics item must use {STATS_INTERVAL_MACRO}")\n',
)

new_trigger_policy = '''def validate_trigger_policy(exports):
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

        if not all(token in short for token in (f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)=3", f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)<30", f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)>0")):
            fail(f"Zabbix {version}: short outage trigger must cover samples 3 through 29")
        if not all(token in long for token in (f"count(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)=30", f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#30)=0")):
            fail(f"Zabbix {version}: long outage trigger must require 30 zero samples")
        if not all(token in loss for token in (f"min(/{TEMPLATE_NAME}/{LOSS_KEY},#2)", f"max(/{TEMPLATE_NAME}/{LOSS_KEY},#2)<100")):
            fail(f"Zabbix {version}: packet loss trigger must use two degraded non-total-loss samples")
        if f"avg(/{TEMPLATE_NAME}/{AVG_KEY},5m)" not in response or f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0" not in response:
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
                fail(f"Zabbix {version}: advanced trigger {name!r} must depend on collector error and packet loss")
            if f"max(/{TEMPLATE_NAME}/{AVAIL_KEY},#3)>0" not in trigger["expression"]:
                fail(f"Zabbix {version}: advanced trigger {name!r} must recover during total outage")

        core_names = {
            "Advanced ICMP: High packet loss",
            "Advanced ICMP: High response time",
            "Advanced ICMP: Long unavailable by ICMP ping",
            "Advanced ICMP: Unavailable by ICMP ping",
        }
        for name in core_names:
            dependency_names = {dependency for dependency, _ in names[name]["dependencies"]}
            if COLLECTOR_ERROR_TRIGGER in dependency_names:
                fail(f"Zabbix {version}: native core trigger {name!r} must not depend on the external collector")

        for trigger in triggers.values():
            if trigger["priority"] == "DISASTER":
                fail(f"Zabbix {version}: resource template must not use DISASTER severity")
            if not any(name == "scope" for name, _ in trigger["tags"]):
                fail(f"Zabbix {version}: trigger {trigger['name']!r} has no scope tag")
'''

validator = re.sub(
    r"def validate_trigger_policy\(exports\):.*?\n\ndef validate_native_template\(exports\):",
    new_trigger_policy + "\n\ndef validate_hybrid_template(exports):",
    validator,
    flags=re.S,
)

new_hybrid_body = '''def validate_hybrid_template(exports):
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
    forbidden_legacy_keys = {"advanced.ping.avg", "advanced.ping.loss", "advanced.ping.rcv", "advanced.ping.xmt"}

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
        if ("MULTIPLIER", ("1000",), "", "") not in normalize_preprocessing(items_by_key[AVG_KEY].get("preprocessing", [])):
            fail(f"Zabbix {version}: native RTT must convert seconds to milliseconds")

        master_key = str(external[0].get("key", ""))
        for key in ("advanced.ping.error", "advanced.ping.jitter", "advanced.ping.max", "advanced.ping.min", "advanced.ping.stddev"):
            item = items_by_key[key]
            if item.get("type") != "DEPENDENT":
                fail(f"Zabbix {version}: advanced statistic {key!r} must be DEPENDENT")
            if str(item.get("master_item", {}).get("key", "")) != master_key:
                fail(f"Zabbix {version}: advanced statistic {key!r} has wrong master item")
            if str(item.get("history", "")) != "30d":
                fail(f"Zabbix {version}: advanced statistic {key!r} must retain 30d history")
        for key in ("advanced.ping.jitter", "advanced.ping.max", "advanced.ping.min", "advanced.ping.stddev"):
            if str(items_by_key[key].get("value_type", "UNSIGNED")) != "FLOAT":
                fail(f"Zabbix {version}: advanced statistic {key!r} must be FLOAT")
        if str(items_by_key["advanced.ping.error"].get("value_type", "UNSIGNED")) != "TEXT":
            fail(f"Zabbix {version}: collector error must be TEXT")

        macros = {m["macro"]: str(m.get("value", "")) for m in template.get("macros", [])}
        for macro, expected in required_macros.items():
            if macros.get(macro) != expected:
                fail(f"Zabbix {version}: macro {macro} must default to {expected}")
'''

validator = re.sub(
    r"def validate_hybrid_template\(exports\):.*?\n\ndef main\(\):",
    new_hybrid_body + "\n\ndef main():",
    validator,
    flags=re.S,
)

new_main = '''def main():
    exports = load_exports(JITTER_TEMPLATE_FILE)
    for version_dir in sorted(TEMPLATES_DIR.glob("zabbix-*")):
        if (version_dir / "advanced-icmp-ping.yaml").exists():
            fail(f"{version_dir.name}: separate native template must not exist; the project ships one hybrid template")

    project_version = validate_version_file(exports)
    validate_cross_version_parity(exports)
    validate_external_script(exports)
    validate_macro_timing(exports)
    validate_collector_float_contract(exports)
    validate_item_tags(exports)
    validate_hybrid_template(exports)
    validate_trigger_policy(exports)

    versions = ", ".join(sorted(exports))
    print(f"OK: single hybrid ICMP template validated for Zabbix {versions}; project version {project_version}")
'''
validator = re.sub(r"def main\(\):.*?\n\nif __name__ == \"__main__\":", new_main + '\n\nif __name__ == "__main__":', validator, flags=re.S)
validator_path.write_text(validator, encoding="utf-8")

pt_deployment = '''# Arquitetura de implantação\n\n[English](../en/deployment-modes.md) | **Português (Brasil)**\n\nO projeto usa **um único template híbrido**: `Advanced ICMP Ping with Jitter`.\n\n## Caminho principal — nativo e escalável\n\nA cada minuto o Zabbix usa seus checks `SIMPLE` nativos:\n\n- `icmpping` para disponibilidade;\n- `icmppingloss` para perda de pacotes;\n- `icmppingsec` em modo `avg` para RTT médio.\n\nEsses checks são processados pelos ICMP pingers do Zabbix server/proxy. Destinos com parâmetros compatíveis podem ser agrupados pelo `fping`, evitando um processo Python por host no caminho de monitoramento que determina estado, perda e latência média.\n\n## Estatística avançada — integrada ao mesmo template\n\nO mesmo template mantém um único item `EXTERNAL`, mas em frequência menor, controlada por `{$ADV_ICMP_STATS_INTERVAL}` (padrão `5m`). Ele existe apenas para métricas que o ICMP nativo não fornece a partir dos RTTs individuais do mesmo lote:\n\n- jitter pacote a pacote;\n- desvio padrão do RTT;\n- RTT mínimo e máximo do mesmo lote de amostras.\n\nSe o coletor avançado falhar, o item `Collector error` alerta, porém disponibilidade, perda e RTT médio continuam sendo medidos pelo ICMP nativo e não dependem do Python.\n\n## Escala\n\nPara ambientes maiores, mantenha o core em `1m` e aumente apenas `{$ADV_ICMP_STATS_INTERVAL}` para `10m` ou `15m` se a estatística avançada não precisar de alta frequência. Assim, a sensibilidade do estado do dispositivo permanece em aproximadamente 3 minutos, enquanto a carga de external checks pode ser reduzida de forma independente.\n'''

en_deployment = '''# Deployment architecture\n\n**English** | [Português (Brasil)](../pt-BR/deployment-modes.md)\n\nThe project ships **one hybrid template**: `Advanced ICMP Ping with Jitter`.\n\n## Primary path — native and scalable\n\nEvery minute Zabbix uses its native `SIMPLE` checks:\n\n- `icmpping` for availability;\n- `icmppingloss` for packet loss;\n- `icmppingsec` in `avg` mode for average RTT.\n\nThese checks are handled by the Zabbix server/proxy ICMP pingers. Targets with compatible parameters can be grouped through `fping`, so the monitoring path that determines state, loss and average latency does not start one Python process per host.\n\n## Advanced statistics — integrated in the same template\n\nThe same template retains one lower-frequency `EXTERNAL` item controlled by `{$ADV_ICMP_STATS_INTERVAL}` (default `5m`). It is used only for metrics the native ICMP pinger does not expose from the individual RTTs of the same packet batch:\n\n- packet-to-packet jitter;\n- RTT standard deviation;\n- minimum and maximum RTT from the same sample batch.\n\nIf the advanced collector fails, `Collector error` alerts while availability, packet loss and average RTT continue through the native ICMP path and do not depend on Python.\n\n## Scale\n\nFor larger deployments, keep the native core at `1m` and increase only `{$ADV_ICMP_STATS_INTERVAL}` to `10m` or `15m` when advanced statistics do not require high frequency. Device-state sensitivity remains around three minutes while external-check load can be reduced independently.\n'''
(ROOT / "docs/pt-BR/deployment-modes.md").write_text(pt_deployment, encoding="utf-8")
(ROOT / "docs/en/deployment-modes.md").write_text(en_deployment, encoding="utf-8")

for rel in ("README.pt-BR.md", "README.md"):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if rel.endswith("pt-BR.md"):
        text = re.sub(
            r"Template Zabbix para monitoramento avançado de ICMP.*?\n\n## Compatibilidade",
            "Template Zabbix híbrido para monitoramento ICMP em escala: disponibilidade, perda e RTT médio usam o pinger nativo do Zabbix a cada minuto, enquanto um coletor Python/fping de menor frequência acrescenta jitter, desvio padrão e min/max do mesmo lote de RTTs.\n\nA arquitetura usa **um único template** e mantém o caminho de disponibilidade independente do coletor externo.\n\n## Compatibilidade",
            text,
            count=1,
            flags=re.S,
        )
        text = text.replace("advanced_icmp_ping.py 8.8.8.8 20 100 1000", "advanced_icmp_ping.py 8.8.8.8 20 250 250")
    else:
        text = re.sub(
            r"Zabbix template for advanced ICMP monitoring.*?\n\n## Compatibility",
            "Hybrid Zabbix ICMP template built for scale: availability, packet loss and average RTT use the native Zabbix ICMP pinger every minute, while a lower-frequency Python/fping collector adds jitter, RTT standard deviation and same-batch min/max statistics.\n\nThe architecture ships as **one template** and keeps device availability independent of the external collector.\n\n## Compatibility",
            text,
            count=1,
            flags=re.S,
        )
        text = text.replace("advanced_icmp_ping.py 8.8.8.8 20 100 1000", "advanced_icmp_ping.py 8.8.8.8 20 250 250")
    path.write_text(text, encoding="utf-8")

for lang in ("pt-BR", "en"):
    path = ROOT / f"docs/{lang}/configuration.md"
    text = path.read_text(encoding="utf-8")
    if lang == "pt-BR":
        text = text.replace(
            "O External check mestre possui intervalo de atualização explícito de `1m`. Portanto, as janelas dos triggers baseadas em quantidade de coletas correspondem aproximadamente a:\n\n```text\n#3  = aproximadamente 3 minutos\n#30 = aproximadamente 30 minutos\n```",
            "Os checks nativos de disponibilidade, perda e RTT médio usam intervalo de `1m`. Portanto, as janelas de indisponibilidade correspondem aproximadamente a:\n\n```text\n#3  = aproximadamente 3 minutos\n#30 = aproximadamente 30 minutos\n```\n\nO External check de estatística avançada não determina o estado do host. Ele usa `{$ADV_ICMP_STATS_INTERVAL}`, com padrão `5m`, somente para jitter, desvio padrão e min/max do mesmo lote.",
        )
        text = text.replace("| `{$ADV_ICMP_JITTER_WARN}` | `20` |", "| `{$ADV_ICMP_STATS_INTERVAL}` | `5m` | Intervalo do coletor externo de estatísticas avançadas. |\n| `{$ADV_ICMP_JITTER_WARN}` | `20` |")
    else:
        text = text.replace(
            "The master External check has an explicit `1m` update interval. Therefore, trigger windows based on collected-value counts correspond approximately to:\n\n```text\n#3  = approximately 3 minutes\n#30 = approximately 30 minutes\n```",
            "The native availability, loss and average RTT checks use a `1m` interval. Therefore, outage windows correspond approximately to:\n\n```text\n#3  = approximately 3 minutes\n#30 = approximately 30 minutes\n```\n\nThe advanced-statistics External check does not determine host state. It uses `{$ADV_ICMP_STATS_INTERVAL}`, default `5m`, only for jitter, standard deviation and same-batch min/max.",
        )
        text = text.replace("| `{$ADV_ICMP_JITTER_WARN}` | `20` |", "| `{$ADV_ICMP_STATS_INTERVAL}` | `5m` | Advanced external statistics collection interval. |\n| `{$ADV_ICMP_JITTER_WARN}` | `20` |")
    path.write_text(text, encoding="utf-8")

pt_tuning = ROOT / "docs/pt-BR/tuning.md"
text = pt_tuning.read_text(encoding="utf-8")
text = re.sub(
    r"## Escala do ambiente.*?## Ajuste de triggers",
    "## Escala do ambiente\n\nO template é híbrido e único. Disponibilidade, perda e RTT médio usam o ICMP pinger nativo a cada `1m`; jitter, desvio padrão e min/max do mesmo lote usam o coletor externo em `{$ADV_ICMP_STATS_INTERVAL}` (padrão `5m`).\n\nPara aumentar a escala sem perder sensibilidade de estado:\n\n- mantenha o caminho nativo em `1m`;\n- aumente `{$ADV_ICMP_STATS_INTERVAL}` para `10m` ou `15m` quando a estatística avançada puder ser menos frequente;\n- distribua hosts entre proxies quando necessário;\n- acompanhe utilização de ICMP pingers e pollers de external checks;\n- aumente `POOL_COUNT` somente quando o ganho estatístico justificar o custo.\n\n## Ajuste de triggers",
    text,
    flags=re.S,
)
text = re.sub(
    r"## Retenção.*",
    "## Retenção\n\nOs itens numéricos do template usam por padrão 30 dias de histórico e o JSON bruto do coletor avançado mantém 1 hora. Ajuste a retenção conforme a escala do banco e a necessidade de análise forense.\n",
    text,
    flags=re.S,
)
pt_tuning.write_text(text, encoding="utf-8")

en_tuning = ROOT / "docs/en/tuning.md"
text = en_tuning.read_text(encoding="utf-8")
text = re.sub(
    r"## Environment scale.*?## Trigger tuning",
    "## Environment scale\n\nThe project ships one hybrid template. Availability, loss and average RTT use the native ICMP pinger every `1m`; packet-level jitter, standard deviation and same-batch min/max use the external collector at `{$ADV_ICMP_STATS_INTERVAL}` (default `5m`).\n\nTo scale without losing device-state sensitivity:\n\n- keep the native path at `1m`;\n- increase `{$ADV_ICMP_STATS_INTERVAL}` to `10m` or `15m` when advanced statistics may run less frequently;\n- distribute hosts across proxies when needed;\n- monitor ICMP pinger and external-check poller utilization;\n- increase `POOL_COUNT` only when the statistical benefit justifies the cost.\n\n## Trigger tuning",
    text,
    flags=re.S,
)
text = re.sub(
    r"## Retention.*",
    "## Retention\n\nNumeric items keep 30 days of history by default and the advanced raw JSON keeps one hour. Tune retention according to database scale and forensic requirements.\n",
    text,
    flags=re.S,
)
en_tuning.write_text(text, encoding="utf-8")

# Remove this one-shot helper from the resulting commit.
Path(__file__).unlink()
