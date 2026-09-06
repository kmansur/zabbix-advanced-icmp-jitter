#!/usr/bin/env python3
"""One-shot helper for the native ICMP/review checkpoint."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# Preserve fractional packet loss in the external collector template.
loss_pattern = re.compile(
    r"(      key: advanced\.ping\.loss\n(?:      delay: '0'\n)?      history: 90d\n)"
    r"(      units: '%')"
)
for version in ("7.0", "8.0"):
    path = ROOT / f"templates/zabbix-{version}/advanced-icmp-ping-with-jitter.yaml"
    text = path.read_text(encoding="utf-8")
    if "key: advanced.ping.loss" not in text:
        raise SystemExit(f"{path}: packet-loss item not found")
    if re.search(
        r"key: advanced\.ping\.loss\n(?:      delay: '0'\n)?      history: 90d\n"
        r"      value_type: FLOAT\n",
        text,
    ) is None:
        text, count = loss_pattern.subn(r"\1      value_type: FLOAT\n\2", text)
        if count != 1:
            raise SystemExit(f"{path}: expected one packet-loss item, changed {count}")
        path.write_text(text, encoding="utf-8")


# Harden semantic validation for collector float fields and the lean native template.
validator = ROOT / "tools/validate_templates.py"
text = validator.read_text(encoding="utf-8")
if "def validate_collector_float_contract(exports):" not in text:
    marker = "def validate_item_tags(exports):\n"
    addition = '''def validate_collector_float_contract(exports):
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


'''
    if marker not in text:
        raise SystemExit("validator: item-tag function marker not found")
    text = text.replace(marker, addition + marker, 1)

native_validator = '''def validate_native_template(exports):
    expected_keys = {
        "icmpping[,{$ADV_ICMP_PACKETS},{$ADV_ICMP_INTERVAL_MS},,{$ADV_ICMP_TIMEOUT_MS}]",
        "icmppingloss[,{$ADV_ICMP_PACKETS},{$ADV_ICMP_INTERVAL_MS},,{$ADV_ICMP_TIMEOUT_MS}]",
        "icmppingsec[,{$ADV_ICMP_PACKETS},{$ADV_ICMP_INTERVAL_MS},,{$ADV_ICMP_TIMEOUT_MS},avg]",
    }
    required_macros = {
        "{$ADV_ICMP_PACKETS}": "20",
        "{$ADV_ICMP_INTERVAL_MS}": "250",
        "{$ADV_ICMP_TIMEOUT_MS}": "250",
        "{$ADV_ICMP_LOSS_WARN}": "20",
        "{$ADV_ICMP_RESPONSE_TIME_WARN}": "200",
    }
    for version, (_, data) in exports.items():
        template = get_template(data)
        if template.get("template") != "Advanced ICMP Ping":
            fail(f"Zabbix {version}: unexpected native template name")

        items = template.get("items", [])
        keys = {str(item.get("key", "")) for item in items}
        if len(items) != 3 or keys != expected_keys:
            fail(
                f"Zabbix {version}: native template must contain exactly "
                "availability, loss and average RTT"
            )
        if any(item.get("type") != "SIMPLE" for item in items):
            fail(f"Zabbix {version}: native ICMP items must all use SIMPLE checks")

        for item in items:
            if str(item.get("delay", "")) != "1m":
                fail(
                    f"Zabbix {version}: native ICMP item {item.get('key')!r} "
                    "must use 1m interval"
                )
            if str(item.get("history", "")) != "30d":
                fail(
                    f"Zabbix {version}: native ICMP item {item.get('key')!r} "
                    "must use 30d history"
                )
            key = str(item.get("key", ""))
            if key.startswith(("icmppingloss", "icmppingsec")):
                if str(item.get("value_type", "UNSIGNED")) != "FLOAT":
                    fail(f"Zabbix {version}: native item {key!r} must declare value_type FLOAT")
            if key.startswith("icmppingsec"):
                steps = normalize_preprocessing(item.get("preprocessing", []))
                if ("MULTIPLIER", ("1000",), "", "") not in steps:
                    fail(
                        f"Zabbix {version}: native RTT item {key!r} "
                        "must convert seconds to milliseconds"
                    )

        macros = {m["macro"]: str(m.get("value", "")) for m in template.get("macros", [])}
        for macro, expected in required_macros.items():
            if macros.get(macro) != expected:
                fail(f"Zabbix {version}: native macro {macro} must default to {expected}")

        triggers = {
            trigger["name"]: trigger for trigger in collect_trigger_nodes(data).values()
        }
        required_triggers = {
            "Advanced ICMP: Unavailable by ICMP ping",
            "Advanced ICMP: Long unavailable by ICMP ping",
            "Advanced ICMP: High packet loss",
            "Advanced ICMP: High response time",
        }
        if set(triggers) != required_triggers:
            fail(f"Zabbix {version}: native template trigger set differs from policy")

        short = triggers["Advanced ICMP: Unavailable by ICMP ping"]["expression"]
        long = triggers["Advanced ICMP: Long unavailable by ICMP ping"]["expression"]
        loss = triggers["Advanced ICMP: High packet loss"]["expression"]
        response = triggers["Advanced ICMP: High response time"]["expression"]

        if not all(
            token in short
            for token in (
                "count(/Advanced ICMP Ping/icmpping[",
                ",#3)=3",
                ",#30)<30",
                ",#30)>0",
            )
        ):
            fail(
                f"Zabbix {version}: short outage trigger must require 3 samples "
                "and stop at the 30-sample outage"
            )
        if not all(
            token in long
            for token in (
                "count(/Advanced ICMP Ping/icmpping[",
                ",#30)=30",
                "max(/Advanced ICMP Ping/icmpping[",
                ",#30)=0",
            )
        ):
            fail(
                f"Zabbix {version}: long outage trigger must require "
                "30 collected zero samples"
            )
        if not all(
            token in loss
            for token in (
                ",#2)>{$ADV_ICMP_LOSS_WARN}",
                "max(/Advanced ICMP Ping/icmppingloss[",
                ",#2)<100",
            )
        ):
            fail(
                f"Zabbix {version}: native packet loss trigger must require "
                "two degraded, non-total-loss samples"
            )
        if "max(/Advanced ICMP Ping/icmpping[" not in response or ",#3)>0" not in response:
            fail(
                f"Zabbix {version}: response-time trigger must recover/suppress "
                "during complete unavailability"
            )

        for trigger in triggers.values():
            if trigger["priority"] == "DISASTER":
                fail(f"Zabbix {version}: native template must not use DISASTER severity")
            if not any(name == "scope" for name, _ in trigger["tags"]):
                fail(f"Zabbix {version}: native trigger {trigger['name']!r} has no scope tag")
'''
text, count = re.subn(
    r"def validate_native_template\(exports\):.*?(?=\n\ndef main\(\):)",
    native_validator.rstrip(),
    text,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"validator: expected one native validator, changed {count}")

call = "    validate_collector_float_contract(jitter_exports)\n"
if call not in text:
    anchor = "    validate_macro_timing(jitter_exports)\n"
    if anchor not in text:
        raise SystemExit("validator: jitter timing call not found")
    text = text.replace(anchor, anchor + call, 1)
validator.write_text(text, encoding="utf-8")


# Regression test for fractional packet-loss precision.
tests = ROOT / "tests/test_advanced_icmp_ping.py"
text = tests.read_text(encoding="utf-8")
addition = '''def test_stats_preserves_fractional_packet_loss():
    result = advanced_icmp_ping.stats([10.0, None, 12.0, 14.0, None, 16.0, 18.0])

    assert result["loss"] == 28.571
    assert isinstance(result["loss"], float)


'''
if "def test_stats_preserves_fractional_packet_loss():" not in text:
    anchor = "def test_stats_with_total_loss():\n"
    if anchor not in text:
        raise SystemExit("tests: total-loss test marker not found")
    text = text.replace(anchor, addition + anchor, 1)
tests.write_text(text, encoding="utf-8")


# Correct stale timing examples and document scale/retention.
for rel, language in (("docs/en/tuning.md", "en"), ("docs/pt-BR/tuning.md", "pt")):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "{$ADV_FPING_INTERVAL_MS}=100\n{$ADV_FPING_TIMEOUT_MS}=1000",
        "{$ADV_FPING_INTERVAL_MS}=250\n{$ADV_FPING_TIMEOUT_MS}=250",
        1,
    )
    text = text.replace(
        "{$ADV_FPING_INTERVAL_MS}=50\n{$ADV_ICMP_JITTER_WARN}",
        "{$ADV_FPING_INTERVAL_MS}=50\n{$ADV_FPING_TIMEOUT_MS}=50\n{$ADV_ICMP_JITTER_WARN}",
        1,
    )
    text = text.replace(
        "{$ADV_FPING_INTERVAL_MS}=100\n{$ADV_ICMP_JITTER_WARN}",
        "{$ADV_FPING_INTERVAL_MS}=100\n{$ADV_FPING_TIMEOUT_MS}=100\n{$ADV_ICMP_JITTER_WARN}",
        1,
    )
    text = text.replace(
        "{$ADV_FPING_INTERVAL_MS}=50\n{$ADV_ICMP_JITTER_WARN}",
        "{$ADV_FPING_INTERVAL_MS}=50\n{$ADV_FPING_TIMEOUT_MS}=50\n{$ADV_ICMP_JITTER_WARN}",
        1,
    )

    if language == "en":
        old = "## Environment scale\n\nOn servers or proxies monitoring many hosts:\n"
        new = (
            "## Environment scale\n\n"
            "For broad ICMP availability, packet-loss and average-RTT monitoring, prefer "
            "the `Advanced ICMP Ping` native template. Zabbix can batch targets that share "
            "identical ICMP parameters through dedicated pinger processes. Reserve "
            "`Advanced ICMP Ping with Jitter` for selected paths where jitter and RTT "
            "standard deviation justify a per-host external collector.\n\n"
            "On servers or proxies monitoring many hosts with the jitter template:\n"
        )
        retention = (
            "\n## Retention\n\n"
            "The native template defaults to 30 days of raw history. The jitter template "
            "currently keeps 90 days for numeric metrics and 1 hour for raw JSON. Reduce "
            "raw history where database scale is more important than high-resolution "
            "forensic analysis; numeric trends preserve long-term behavior at much lower "
            "storage cost.\n"
        )
    else:
        old = "## Escala do ambiente\n\nEm servidores ou proxies que monitoram muitos hosts:\n"
        new = (
            "## Escala do ambiente\n\n"
            "Para monitoramento amplo de disponibilidade ICMP, perda e RTT médio, prefira "
            "o template nativo `Advanced ICMP Ping`. O Zabbix consegue agrupar alvos que "
            "compartilham parâmetros ICMP idênticos nos processos dedicados de pinger. "
            "Reserve `Advanced ICMP Ping with Jitter` para caminhos selecionados onde "
            "jitter e desvio padrão de RTT justifiquem um coletor externo por host.\n\n"
            "Em servidores ou proxies que monitoram muitos hosts com o template de jitter:\n"
        )
        retention = (
            "\n## Retenção\n\n"
            "O template nativo usa por padrão 30 dias de histórico bruto. O template de "
            "jitter atualmente mantém 90 dias para métricas numéricas e 1 hora para o JSON "
            "bruto. Reduza o histórico bruto quando a escala do banco for mais importante "
            "que análise forense em alta resolução; trends numéricos preservam o comportamento "
            "de longo prazo com custo muito menor.\n"
        )
    if old in text:
        text = text.replace(old, new, 1)
    if "## Retention" not in text and "## Retenção" not in text:
        text += retention
    path.write_text(text, encoding="utf-8")


# Deployment-mode guide.
(ROOT / "docs/en/deployment-modes.md").write_text(
    """# Deployment modes

[English](deployment-modes.md) | [Português (Brasil)](../pt-BR/deployment-modes.md)

The project provides two complementary monitoring modes.

## Advanced ICMP Ping — native, scalable default

Use `advanced-icmp-ping.yaml` for broad deployment. It uses Zabbix `SIMPLE` checks:

- `icmpping` for reachability;
- `icmppingloss` for packet loss;
- `icmppingsec` in `avg` mode for average RTT.

All three run through the Zabbix server/proxy ICMP pinger. Targets with identical parameters can be grouped and checked by `fping` in parallel, avoiding a Python process per monitored host. The default update interval is one minute, with short unavailability at about 3 minutes and long unavailability at about 30 minutes.

## Advanced ICMP Ping with Jitter — selective advanced statistics

Use `advanced-icmp-ping-with-jitter.yaml` where you need individual RTT samples, jitter, population standard deviation, or min/max from the same packet batch. Its master item is an `EXTERNAL` check: the Zabbix server/proxy starts the Python collector, which starts `fping`, for each linked host and collection cycle.

Typical selective targets include WAN gateways, site-to-site links, firewalls, edge routers, voice/video paths, and links under troubleshooting.

Do not link both templates to the same host unless you intentionally want both native baseline monitoring and the additional external statistical workload.
""",
    encoding="utf-8",
)
(ROOT / "docs/pt-BR/deployment-modes.md").write_text(
    """# Modos de implantação

[English](../en/deployment-modes.md) | **Português (Brasil)**

O projeto oferece dois modos complementares de monitoramento.

## Advanced ICMP Ping — padrão nativo e escalável

Use `advanced-icmp-ping.yaml` para aplicação ampla. Ele usa checks `SIMPLE` nativos do Zabbix:

- `icmpping` para disponibilidade;
- `icmppingloss` para perda de pacotes;
- `icmppingsec` em modo `avg` para RTT médio.

Os três são executados pelos processos ICMP pinger do Zabbix server/proxy. Alvos com parâmetros idênticos podem ser agrupados e verificados pelo `fping` em paralelo, evitando um processo Python por host monitorado. O intervalo padrão é de um minuto, com indisponibilidade curta em aproximadamente 3 minutos e prolongada em aproximadamente 30 minutos.

## Advanced ICMP Ping with Jitter — estatística avançada seletiva

Use `advanced-icmp-ping-with-jitter.yaml` onde forem necessárias amostras individuais de RTT, jitter, desvio padrão populacional ou min/max do mesmo lote de pacotes. Seu item mestre é um check `EXTERNAL`: o Zabbix server/proxy inicia o coletor Python, que inicia o `fping`, para cada host vinculado e ciclo de coleta.

Alvos típicos incluem gateways WAN, enlaces entre sites, firewalls, roteadores de borda, caminhos de voz/vídeo e enlaces em troubleshooting.

Não vincule os dois templates ao mesmo host, a menos que queira intencionalmente o baseline nativo e também a carga estatística externa adicional.
""",
    encoding="utf-8",
)

for rel, marker, link in (
    (
        "docs/en/README.md",
        "## Documentation\n\n",
        "- [Deployment modes: native vs. jitter](deployment-modes.md)\n",
    ),
    (
        "docs/pt-BR/README.md",
        "## Documentação\n\n",
        "- [Modos de implantação: nativo vs. jitter](deployment-modes.md)\n",
    ),
):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if link not in text:
        if marker not in text:
            raise SystemExit(f"{rel}: documentation section marker not found")
        text = text.replace(marker, marker + link, 1)
    path.write_text(text, encoding="utf-8")


# Make execution location and deployment choice explicit in installation docs.
for rel, language in (("docs/en/installation.md", "en"), ("docs/pt-BR/installation.md", "pt")):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if language == "en":
        heading = "## Choose the deployment mode"
        block = '''## Choose the deployment mode

For most hosts, import and use `advanced-icmp-ping.yaml`. It needs `fping` on the Zabbix server/proxy but does not require the Python external collector. Use `advanced-icmp-ping-with-jitter.yaml` only for selected targets that need jitter or RTT standard deviation.

The jitter template executes the `EXTERNAL` master item on the Zabbix server/proxy, not on the monitored host. Each linked host therefore starts one Python/`fping` collector execution per collection cycle.

'''
        anchor = "## Installing dependencies\n"
    else:
        heading = "## Escolha do modo de implantação"
        block = '''## Escolha do modo de implantação

Para a maioria dos hosts, importe e use `advanced-icmp-ping.yaml`. Ele precisa do `fping` no Zabbix server/proxy, mas não exige o coletor externo Python. Use `advanced-icmp-ping-with-jitter.yaml` somente nos alvos selecionados que precisam de jitter ou desvio padrão de RTT.

O template de jitter executa o item mestre `EXTERNAL` no Zabbix server/proxy, não no host monitorado. Portanto, cada host vinculado inicia uma execução Python/`fping` por ciclo de coleta.

'''
        anchor = "## Instalação das dependências\n"
    if heading not in text:
        if anchor not in text:
            raise SystemExit(f"{rel}: dependency heading not found")
        text = text.replace(anchor, block + anchor, 1)
    path.write_text(text, encoding="utf-8")


# Package both template variants for each maintained Zabbix version.
release = ROOT / ".github/workflows/release.yml"
text = release.read_text(encoding="utf-8")
old = (
    "            cp templates/zabbix-${zabbix_version}/advanced-icmp-ping-with-jitter.yaml \\\n"
    "               \"$root/templates/zabbix-${zabbix_version}/\"\n"
)
new = (
    "            cp templates/zabbix-${zabbix_version}/*.yaml \\\n"
    "               \"$root/templates/zabbix-${zabbix_version}/\"\n"
)
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("release workflow template-copy block not found")
release.write_text(text, encoding="utf-8")


# This helper is intentionally removed by the checkpoint commit.
Path(__file__).unlink()
