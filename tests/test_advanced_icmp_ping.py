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


def test_main_returns_expected_json(monkeypatch, capsys):
    class Completed:
        stdout = ""
        stderr = "8.8.8.8 : 10.0 12.0 11.0 13.0\n"

    monkeypatch.setattr(advanced_icmp_ping.subprocess, "run", lambda *args, **kwargs: Completed())
    monkeypatch.setattr(
        advanced_icmp_ping.sys,
        "argv",
        ["advanced_icmp_ping.py", "8.8.8.8", "4", "100", "1000"],
    )

    advanced_icmp_ping.main()
    result = json.loads(capsys.readouterr().out)

    assert result["target"] == "8.8.8.8"
    assert result["xmt"] == 4
    assert result["rcv"] == 4
    assert result["loss"] == 0.0
    assert result["jitter"] == 1.667


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
