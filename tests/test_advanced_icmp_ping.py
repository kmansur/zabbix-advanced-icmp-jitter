import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "advanced_icmp_ping.py"
FIXTURES = ROOT / "tests" / "fixtures"

spec = importlib.util.spec_from_file_location("advanced_icmp_ping", SCRIPT_PATH)
advanced_icmp_ping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(advanced_icmp_ping)


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_successful_ipv4_batch():
    samples = advanced_icmp_ping.parse_fping_output(fixture("fping-success.txt"), 4)
    assert samples == [10.0, 12.0, 11.0, 13.0]


def test_parse_partial_packet_loss():
    samples = advanced_icmp_ping.parse_fping_output(fixture("fping-packet-loss.txt"), 4)
    assert samples == [10.0, None, 12.0, None]


def test_parse_unreachable_target():
    samples = advanced_icmp_ping.parse_fping_output(fixture("fping-unreachable.txt"), 4)
    assert samples == [None, None, None, None]


def test_parse_ipv6_target_without_splitting_address_colons():
    samples = advanced_icmp_ping.parse_fping_output(fixture("fping-ipv6.txt"), 4)
    assert samples == [10.0, 11.0, None, 12.0]


def test_reject_malformed_fping_sample_line():
    assert advanced_icmp_ping.parse_fping_output(fixture("fping-malformed.txt"), 3) == []


def test_expected_count_candidate_is_preferred():
    output = "\n".join(
        [
            "8.8.8.8 : 1.0 2.0",
            "8.8.8.8 : 10.0 11.0 12.0 13.0",
        ]
    )
    assert advanced_icmp_ping.parse_fping_output(output, 4) == [10.0, 11.0, 12.0, 13.0]


def test_stats_with_partial_loss():
    result = advanced_icmp_ping.stats([10.0, None, 12.0, 14.0])

    assert result["xmt"] == 4
    assert result["rcv"] == 3
    assert result["loss"] == 25.0
    assert result["min"] == 10.0
    assert result["avg"] == 12.0
    assert result["max"] == 14.0
    assert result["jitter"] == 2.0
    assert result["stddev"] == 1.633
    assert result["rtts"] == [10.0, 12.0, 14.0]


def test_stats_with_total_loss():
    result = advanced_icmp_ping.stats([None, None, None, None])

    assert result == {
        "error": "",
        "xmt": 4,
        "rcv": 0,
        "loss": 100.0,
        "min": 0,
        "avg": 0,
        "max": 0,
        "jitter": 0,
        "stddev": 0,
        "rtts": [],
    }


def test_parse_int_defaults_and_clamps():
    assert advanced_icmp_ping.parse_int(None, 20, 2, 100) == 20
    assert advanced_icmp_ping.parse_int("invalid", 20, 2, 100) == 20
    assert advanced_icmp_ping.parse_int("1", 20, 2, 100) == 2
    assert advanced_icmp_ping.parse_int("200", 20, 2, 100) == 100
    assert advanced_icmp_ping.parse_int("30", 20, 2, 100) == 30


def test_target_validation():
    assert advanced_icmp_ping.validate_target("8.8.8.8") == ""
    assert advanced_icmp_ping.validate_target("2001:db8::1") == ""
    assert advanced_icmp_ping.validate_target("host-name.example") == ""
    assert advanced_icmp_ping.validate_target("-v") == "target must not start with '-'"
    assert "whitespace" in advanced_icmp_ping.validate_target("bad host")
    assert "too long" in advanced_icmp_ping.validate_target("a" * 254)


def test_probe_config_rejects_timeout_larger_than_period():
    error = advanced_icmp_ping.validate_probe_config(20, 100, 1000)
    assert "timeout must not exceed probe interval" in error


def test_probe_config_rejects_runtime_over_budget():
    error = advanced_icmp_ping.validate_probe_config(100, 250, 250)
    assert "exceeds collector runtime budget" in error


def test_probe_config_accepts_default_profile():
    assert (
        advanced_icmp_ping.validate_probe_config(
            advanced_icmp_ping.DEFAULT_COUNT,
            advanced_icmp_ping.DEFAULT_INTERVAL_MS,
            advanced_icmp_ping.DEFAULT_TIMEOUT_MS,
        )
        == ""
    )


def test_main_returns_expected_json(monkeypatch, capsys):
    class Completed:
        stdout = ""
        stderr = "8.8.8.8 : 10.0 12.0 11.0 13.0\n"
        returncode = 0

    monkeypatch.setattr(advanced_icmp_ping.subprocess, "run", lambda *args, **kwargs: Completed())
    monkeypatch.setattr(
        advanced_icmp_ping.sys,
        "argv",
        ["advanced_icmp_ping.py", "8.8.8.8", "4", "250", "250"],
    )

    advanced_icmp_ping.main()
    result = json.loads(capsys.readouterr().out)

    assert result["target"] == "8.8.8.8"
    assert result["xmt"] == 4
    assert result["rcv"] == 4
    assert result["loss"] == 0.0
    assert result["jitter"] == 1.667


def test_main_uses_safe_defaults_and_c_locale(monkeypatch, capsys):
    captured = {}

    class Completed:
        stdout = ""
        stderr = ""
        returncode = 0

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return Completed()

    monkeypatch.setattr(advanced_icmp_ping.subprocess, "run", fake_run)
    monkeypatch.setattr(
        advanced_icmp_ping,
        "parse_fping_output",
        lambda output, expected_count=None: [1.0] * expected_count,
    )
    monkeypatch.setattr(advanced_icmp_ping.sys, "argv", ["advanced_icmp_ping.py", "127.0.0.1"])

    advanced_icmp_ping.main()
    result = json.loads(capsys.readouterr().out)

    assert captured["command"] == [
        "fping",
        "-q",
        "-C",
        "20",
        "-p",
        "250",
        "-t",
        "250",
        "127.0.0.1",
    ]
    assert captured["kwargs"]["env"]["LC_ALL"] == "C"
    assert captured["kwargs"]["env"]["LANG"] == "C"
    assert captured["kwargs"]["timeout"] < 30
    assert result["xmt"] == 20


def test_main_rejects_unsafe_timing_before_fping(monkeypatch, capsys):
    monkeypatch.setattr(
        advanced_icmp_ping.sys,
        "argv",
        ["advanced_icmp_ping.py", "8.8.8.8", "20", "100", "1000"],
    )

    with pytest.raises(SystemExit) as excinfo:
        advanced_icmp_ping.main()

    assert excinfo.value.code == 0
    result = json.loads(capsys.readouterr().out)
    assert "timeout must not exceed probe interval" in result["error"]


def test_main_returns_json_when_fping_is_missing(monkeypatch, capsys):
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(advanced_icmp_ping.subprocess, "run", raise_missing)
    monkeypatch.setattr(advanced_icmp_ping.sys, "argv", ["advanced_icmp_ping.py", "8.8.8.8"])

    with pytest.raises(SystemExit) as excinfo:
        advanced_icmp_ping.main()

    assert excinfo.value.code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["error"] == "fping command not found"
    assert result["loss"] == 100


def test_main_returns_json_on_permission_error(monkeypatch, capsys):
    def raise_permission(*args, **kwargs):
        raise PermissionError

    monkeypatch.setattr(advanced_icmp_ping.subprocess, "run", raise_permission)
    monkeypatch.setattr(advanced_icmp_ping.sys, "argv", ["advanced_icmp_ping.py", "8.8.8.8"])

    with pytest.raises(SystemExit):
        advanced_icmp_ping.main()

    result = json.loads(capsys.readouterr().out)
    assert result["error"] == "permission denied while executing fping"


def test_main_returns_json_on_timeout(monkeypatch, capsys):
    def raise_timeout(*args, **kwargs):
        raise advanced_icmp_ping.subprocess.TimeoutExpired(cmd="fping", timeout=1)

    monkeypatch.setattr(advanced_icmp_ping.subprocess, "run", raise_timeout)
    monkeypatch.setattr(advanced_icmp_ping.sys, "argv", ["advanced_icmp_ping.py", "8.8.8.8"])

    with pytest.raises(SystemExit):
        advanced_icmp_ping.main()

    result = json.loads(capsys.readouterr().out)
    assert result["error"] == "fping command timed out"


def test_main_translates_fping_resolution_error(monkeypatch, capsys):
    class Completed:
        stdout = ""
        stderr = ""
        returncode = 2

    monkeypatch.setattr(advanced_icmp_ping.subprocess, "run", lambda *args, **kwargs: Completed())
    monkeypatch.setattr(
        advanced_icmp_ping.sys,
        "argv",
        ["advanced_icmp_ping.py", "invalid.example"],
    )

    with pytest.raises(SystemExit):
        advanced_icmp_ping.main()

    result = json.loads(capsys.readouterr().out)
    assert result["error"] == "fping could not resolve target"
