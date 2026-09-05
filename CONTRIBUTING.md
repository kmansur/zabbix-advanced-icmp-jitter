# Contributing

Contributions, bug reports, documentation improvements, and compatibility updates are welcome.

## Development workflow

1. Create a branch from `main`.
2. Make one focused change.
3. Run the local validation commands.
4. Update documentation when behavior, installation, or compatibility changes.
5. Update `CHANGELOG.md` when the change is user-visible.
6. Open a pull request.

Recommended branch names:

- `feature/<description>`
- `fix/<description>`
- `docs/<description>`
- `refactor/<description>`
- `ci/<description>`
- `chore/<description>`

## Commit messages

Use Conventional Commits when practical:

- `feat:` new functionality;
- `fix:` bug fix;
- `docs:` documentation;
- `refactor:` internal restructuring without behavior change;
- `test:` tests and fixtures;
- `ci:` CI/CD changes;
- `chore:` repository maintenance.

## Local validation

Create and activate a virtual environment if desired, then install the development tools:

```sh
python -m pip install -r requirements-dev.txt
```

Run:

```sh
python -m compileall -q scripts tools tests
ruff check scripts tools tests
ruff format --check scripts tools tests
pytest -q
python tools/validate_templates.py
```

The pull request CI runs the same checks.

## Zabbix template rules

Version-specific exports belong under:

```text
templates/zabbix-<major.minor>/
```

Examples:

```text
templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml
templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml
```

When adding or refreshing a Zabbix export:

1. import the currently maintained template into the target Zabbix build;
2. confirm that collection, dependent items, triggers, dashboard, and graph work;
3. export the template from that Zabbix frontend;
4. store the export in the matching version directory;
5. run `python tools/validate_templates.py`;
6. document the exact Zabbix build used for validation.

The validator intentionally allows serialization differences between Zabbix versions but requires important semantic identifiers to remain aligned, including template UUID, item keys/UUIDs, macros, triggers, dashboards, graphs, and vendor version.

## Versioning

The current historical project version is:

```text
1.0-10
```

It is kept unchanged during this repository-only reorganization so the tested Zabbix exports are not modified unnecessarily.

The next **functional** release should transition to Semantic Versioning (`MAJOR.MINOR.PATCH`), for example `1.0.11` or `1.1.0`, depending on the scope of the change. From that point onward:

- `PATCH` = backward-compatible fixes;
- `MINOR` = backward-compatible features or metrics;
- `MAJOR` = incompatible changes to keys, macros, behavior, or installation.

For a release, these must agree:

```text
VERSION
Zabbix vendor.version in every maintained export
Git tag (vX.Y.Z)
GitHub Release
```

## Collector changes

The production collector lives at:

```text
scripts/advanced_icmp_ping.py
```

Changes to parsing or statistics should include tests using fixtures under `tests/fixtures/`. Avoid invoking a real network target in unit tests.

The collector currently executes `fping` without invoking a shell. Do not replace this with shell command construction unless there is a strong reason and a dedicated security review.
