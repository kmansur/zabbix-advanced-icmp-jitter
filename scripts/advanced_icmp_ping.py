#!/usr/bin/env python3
"""
Advanced ICMP Ping with Jitter

Author: Karim Mansur
Original inspiration: Advanced ICMP Ping by Dusan Priechodsky
Original project: https://github.com/priechodsky/AdvancedPING
License: GNU General Public License v3.0 (GPL-3.0)

Description:
    External script for the Zabbix 7.0 and 8.0 template exports maintained by
    this project.

    The script runs a single fping batch using "-C" so every ICMP reply time
    is available as an individual RTT sample. It then returns a compact JSON
    document with packet counters, packet loss, latency statistics, jitter,
    standard deviation, and the received RTT list.

    Jitter is calculated as the average absolute difference between consecutive
    received RTT samples:

        jitter = average(abs(current_rtt - previous_rtt))

Requirements:
    - Python 3.9 or newer
    - fping installed and executable by the Zabbix server/proxy user

Example:
    ./advanced_icmp_ping.py 8.8.8.8 20 250 250
"""

import json
import math
import os
import re
import subprocess
import sys

DEFAULT_COUNT = 20
DEFAULT_INTERVAL_MS = 250
DEFAULT_TIMEOUT_MS = 250
MIN_COUNT = 2
MAX_COUNT = 100
MIN_INTERVAL_MS = 10
MAX_INTERVAL_MS = 5000
MIN_TIMEOUT_MS = 10
MAX_TIMEOUT_MS = 5000
PROCESS_MARGIN_MS = 2000
MAX_PROCESS_RUNTIME_MS = 25000
MAX_TARGET_LENGTH = 253


def fail(message):
    """Return valid JSON even when collection fails."""
    print(
        json.dumps(
            {
                "error": message,
                "xmt": 0,
                "rcv": 0,
                "loss": 100,
                "min": 0,
                "avg": 0,
                "max": 0,
                "jitter": 0,
                "stddev": 0,
                "rtts": [],
            },
            separators=(",", ":"),
        )
    )
    sys.exit(0)


def parse_int(value, default, minimum, maximum):
    """Parse an integer CLI argument and clamp it to a safe range."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


def validate_target(target):
    """Return an error string for unsafe/invalid target text, otherwise empty."""
    if not target:
        return "target is empty"
    if len(target) > MAX_TARGET_LENGTH:
        return "target is too long"
    if target.startswith("-"):
        return "target must not start with '-'"
    if any(character.isspace() or ord(character) < 32 for character in target):
        return "target contains whitespace or control characters"
    return ""


def validate_probe_config(count, interval_ms, timeout_ms):
    """Validate fping timing rules and keep the external check within its budget."""
    if timeout_ms > interval_ms:
        return (
            "fping timeout must not exceed probe interval in count mode "
            f"(timeout={timeout_ms}ms, interval={interval_ms}ms)"
        )

    estimated_runtime_ms = count * interval_ms + timeout_ms + PROCESS_MARGIN_MS
    if estimated_runtime_ms > MAX_PROCESS_RUNTIME_MS:
        return (
            "configured probe window exceeds collector runtime budget "
            f"({estimated_runtime_ms}ms > {MAX_PROCESS_RUNTIME_MS}ms)"
        )

    return ""


def parse_fping_output(output, expected_count=None):
    """Extract RTT samples from fping "-q -C" output."""
    candidates = []

    for line in output.splitlines():
        if " : " not in line:
            continue

        _, samples = line.rsplit(" : ", 1)
        tokens = samples.strip().split()
        if not tokens:
            continue

        parsed = []
        valid_line = True
        for token in tokens:
            if token == "-":
                parsed.append(None)
                continue

            match = re.match(r"^([0-9]+(?:\.[0-9]+)?)$", token)
            if match:
                parsed.append(float(match.group(1)))
                continue

            valid_line = False
            break

        if valid_line and parsed:
            candidates.append(parsed)

    if not candidates:
        return []

    if expected_count is not None:
        for candidate in candidates:
            if len(candidate) == expected_count:
                return candidate

    return max(candidates, key=len)


def rounded(value):
    """Round monitoring values to three decimal places."""
    return round(value, 3)


def stats(samples):
    """Calculate packet and latency statistics from parsed RTT samples."""
    received = [sample for sample in samples if sample is not None]
    xmt = len(samples)
    rcv = len(received)
    loss = rounded(((xmt - rcv) / xmt) * 100) if xmt else 100

    if not received:
        return {
            "error": "",
            "xmt": xmt,
            "rcv": 0,
            "loss": loss,
            "min": 0,
            "avg": 0,
            "max": 0,
            "jitter": 0,
            "stddev": 0,
            "rtts": [],
        }

    avg = sum(received) / rcv
    deltas = [abs(received[i] - received[i - 1]) for i in range(1, rcv)]
    jitter = sum(deltas) / len(deltas) if deltas else 0
    variance = sum((sample - avg) ** 2 for sample in received) / rcv

    return {
        "error": "",
        "xmt": xmt,
        "rcv": rcv,
        "loss": loss,
        "min": rounded(min(received)),
        "avg": rounded(avg),
        "max": rounded(max(received)),
        "jitter": rounded(jitter),
        "stddev": rounded(math.sqrt(variance)),
        "rtts": [rounded(sample) for sample in received],
    }


def fping_error_message(returncode):
    """Translate documented fping exit codes into stable collector messages."""
    messages = {
        2: "fping could not resolve target",
        3: "fping rejected command-line arguments",
        4: "fping reported a system call failure",
    }
    return messages.get(returncode, f"fping failed with exit status {returncode}")


def main():
    """Read arguments, execute fping, parse output, and print JSON for Zabbix."""
    if len(sys.argv) < 2:
        fail("missing host argument")

    host = sys.argv[1]
    target_error = validate_target(host)
    if target_error:
        fail(target_error)

    count = parse_int(
        sys.argv[2] if len(sys.argv) > 2 else None,
        DEFAULT_COUNT,
        MIN_COUNT,
        MAX_COUNT,
    )
    interval_ms = parse_int(
        sys.argv[3] if len(sys.argv) > 3 else None,
        DEFAULT_INTERVAL_MS,
        MIN_INTERVAL_MS,
        MAX_INTERVAL_MS,
    )
    timeout_ms = parse_int(
        sys.argv[4] if len(sys.argv) > 4 else None,
        DEFAULT_TIMEOUT_MS,
        MIN_TIMEOUT_MS,
        MAX_TIMEOUT_MS,
    )

    config_error = validate_probe_config(count, interval_ms, timeout_ms)
    if config_error:
        fail(config_error)

    command = [
        "fping",
        "-q",
        "-C",
        str(count),
        "-p",
        str(interval_ms),
        "-t",
        str(timeout_ms),
        host,
    ]

    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    environment["LANG"] = "C"
    process_timeout = (
        count * interval_ms + timeout_ms + PROCESS_MARGIN_MS
    ) / 1000

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=process_timeout,
            env=environment,
        )
    except FileNotFoundError:
        fail("fping command not found")
    except PermissionError:
        fail("permission denied while executing fping")
    except subprocess.TimeoutExpired:
        fail("fping command timed out")
    except OSError as exc:
        fail(f"unable to execute fping: {exc.strerror or exc.__class__.__name__}")

    if completed.returncode >= 2:
        fail(fping_error_message(completed.returncode))

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    samples = parse_fping_output(output, count)
    if not samples:
        fail("unable to parse fping output")

    result = stats(samples)
    result["target"] = host
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
