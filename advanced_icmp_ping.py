#!/usr/bin/env python3
"""
Advanced ICMP Ping with Jitter
Version: 1.0.5

Author: Karim Mansur
Original inspiration: Advanced ICMP Ping by Dusan Priechodsky
Original project: https://github.com/priechodsky/AdvancedPING
License: GNU General Public License v3.0 (GPL-3.0)

Description:
    External script for Zabbix 7.0 templates.

    The script runs a single fping batch using "-C" so every ICMP reply time
    is available as an individual RTT sample. It then returns a compact JSON
    document with packet counters, packet loss, latency statistics, jitter,
    standard deviation, and the received RTT list.

    Jitter is calculated as the average absolute difference between consecutive
    received RTT samples:

        jitter = average(abs(current_rtt - previous_rtt))

    This is more accurate for operational monitoring than estimating jitter
    from "max - min", because it uses the packet-to-packet variation observed
    inside the measurement window.

Requirements:
    - Python 3.6 or newer
    - fping installed and executable by the Zabbix server/proxy user

Example:
    ./advanced_icmp_ping.py 8.8.8.8 20 100 1000
"""

import json
import math
import re
import subprocess
import sys


def fail(message):
    """Return valid JSON even when collection fails.

    Zabbix dependent items expect JSONPath preprocessing to receive a JSON
    object. Returning a stable error payload prevents malformed output from
    breaking every dependent item in a noisy way.
    """
    print(json.dumps({
        "error": message,
        "xmt": 0,
        "rcv": 0,
        "loss": 100,
        "min": 0,
        "avg": 0,
        "max": 0,
        "jitter": 0,
        "stddev": 0,
        "rtts": []
    }, separators=(",", ":")))
    sys.exit(0)


def parse_int(value, default, minimum, maximum):
    """Parse an integer CLI argument and clamp it to a safe range.

    The template macros are user-editable, so this function keeps accidental
    values such as empty strings, negative numbers, or very large counts from
    producing slow or unsafe fping calls.
    """
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


def parse_fping_output(output, expected_count=None):
    """Extract RTT samples from fping "-q -C" output.

    fping usually writes summary output to stderr, not stdout. The caller joins
    both streams and this parser scans every line looking for the compact sample
    list produced by "-C":

        8.8.8.8 : 10.1 10.3 - 11.0
        2001:db8::1 : 10.1 10.3 - 11.0

    A dash means the packet was transmitted but no reply was received. It is
    stored as None so packet loss can be calculated without pretending the RTT
    was zero.

    Some fping builds or manual tests may include verbose lines. To avoid
    parsing those by accident, a valid sample line must contain only numeric RTT
    values or "-". The split is done from the right side using " : " so IPv6
    target addresses are not broken by their internal colons. When the expected
    probe count is known, the parser prefers a candidate line with exactly that
    number of samples.
    """
    candidates = []

    for line in output.splitlines():
        if ":" not in line:
            continue

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
    """Round monitoring values to milliseconds with microsecond-style detail."""
    return round(value, 3)


def stats(samples):
    """Calculate packet and latency statistics from parsed RTT samples.

    The input list contains floats for received replies and None for lost
    packets. Lost packets are included in xmt/loss, but excluded from latency,
    jitter, and standard deviation calculations because there is no RTT value to
    measure.

    Returned fields:
        xmt     - transmitted packet count
        rcv     - received packet count
        loss    - packet loss percentage
        min     - minimum received RTT in milliseconds
        avg     - average received RTT in milliseconds
        max     - maximum received RTT in milliseconds
        jitter  - average absolute delta between consecutive received RTTs
        stddev  - population standard deviation of received RTTs
        rtts    - received RTT samples, useful for troubleshooting
    """
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
            "rtts": []
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
        "rtts": [rounded(sample) for sample in received]
    }


def main():
    """Read arguments, execute fping, parse output, and print JSON for Zabbix."""
    if len(sys.argv) < 2:
        fail("missing host argument")

    # Arguments are intentionally positional because Zabbix external item keys
    # pass macro values as simple script parameters.
    host = sys.argv[1]
    count = parse_int(sys.argv[2] if len(sys.argv) > 2 else None, 10, 2, 100)
    interval_ms = parse_int(sys.argv[3] if len(sys.argv) > 3 else None, 200, 20, 60000)
    timeout_ms = parse_int(sys.argv[4] if len(sys.argv) > 4 else None, 1000, 50, 60000)

    # -q keeps the output compact.
    # -C prints one RTT value per probe, which is required for precise jitter.
    # -p controls spacing between probes, and -t controls per-probe timeout.
    command = [
        "fping",
        "-q",
        "-C", str(count),
        "-p", str(interval_ms),
        "-t", str(timeout_ms),
        host
    ]

    try:
        # The Python timeout is slightly larger than the expected fping runtime.
        # It prevents a stuck fping process from tying up the Zabbix poller.
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=((count * interval_ms) + timeout_ms + 5000) / 1000
        )
    except FileNotFoundError:
        fail("fping command not found")
    except subprocess.TimeoutExpired:
        fail("fping command timed out")

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    samples = parse_fping_output(output, count)
    if not samples:
        fail("unable to parse fping output")

    result = stats(samples)
    result["target"] = host
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
