# Security Policy

## Supported versions

Security fixes are provided for the latest maintained project version.

Current compatibility status:

| Component | Status |
| --- | --- |
| Zabbix 7.0 template | Supported |
| Zabbix 8.0 template | Tested on Zabbix 8.0 Beta 2; revalidated as new Beta/RC/final builds are tested |
| Python collector | Supported with the current template version |

Historical releases may receive fixes only when practical.

## Reporting a vulnerability

Do **not** open a public GitHub issue for a security vulnerability.

Use the repository's private GitHub Security Advisory reporting flow:

`Security` > `Advisories` > `Report a vulnerability`

Include, when possible:

- affected project version;
- Zabbix version and exact build;
- Zabbix Server/Proxy operating system;
- Python and `fping` versions;
- minimal reproduction steps;
- expected and observed behavior;
- potential impact;
- sanitized logs or collector output.

Never include passwords, API tokens, private keys, production credentials, or other secrets in a report.

## Security scope

Security-sensitive areas include:

- handling of host and macro values passed to the external collector;
- construction and execution of the `fping` subprocess;
- parsing of external command output;
- release and CI workflows;
- template changes that could execute unexpected commands or expose sensitive data.

The collector invokes `fping` using an argument list rather than a shell command string. Changes that alter this behavior require additional security review and tests.
