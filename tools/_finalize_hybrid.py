#!/usr/bin/env python3
"""One-shot cleanup for the hybrid ICMP exports and validator."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


for version in ("7.0", "8.0"):
    path = ROOT / f"templates/zabbix-{version}/advanced-icmp-ping-with-jitter.yaml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"\{\$\{([A-Z0-9_]+)\}\}",
        lambda match: "{$" + match.group(1) + "}",
        text,
    )
    data = yaml.safe_load(text)
    text = yaml.dump(
        data,
        Dumper=NoAliasDumper,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    )
    path.write_text(text, encoding="utf-8")

validator = ROOT / "tools/validate_templates.py"
text = validator.read_text(encoding="utf-8")
old = '''        path = version_dir / filename
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
'''
new = '''        path = version_dir / filename
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        raw = path.read_text(encoding="utf-8")
        if "{${" in raw:
            fail(f"{path.relative_to(ROOT)} contains malformed Zabbix user macro syntax")
        if re.search(r"(^|\\s)[&*]id[0-9]+", raw):
            fail(f"{path.relative_to(ROOT)} must not contain YAML aliases/anchors")
        data = yaml.safe_load(raw)
'''
if old not in text:
    raise SystemExit("load_exports block not found")
validator.write_text(text.replace(old, new, 1), encoding="utf-8")

Path(__file__).unlink()
