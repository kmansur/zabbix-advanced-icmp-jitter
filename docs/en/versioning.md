# Versioning

[English](versioning.md) | [Português (Brasil)](../pt-BR/versioning.md)

## Current version

The project currently keeps the historical version:

```text
1.0-10
```

It appears in Zabbix exports as:

```yaml
vendor:
  name: Net Tech
  version: 1.0-10
```

The root `VERSION` file must contain the same value.

This version was not changed during repository reorganization because there was no functional template change and the 7.0/8.0 exports had already been validated with this version number.

## Transition to Semantic Versioning

The next **functional** release should adopt `MAJOR.MINOR.PATCH`.

Examples:

- `1.0.11`: backward-compatible fix;
- `1.1.0`: new backward-compatible feature, item, metric, or trigger;
- `2.0.0`: incompatible change to a key, macro, installation method, or behavior.

After the transition, the project will use:

```text
VERSION                1.1.0
vendor.version          1.1.0
Git tag                 v1.1.0
GitHub Release          v1.1.0
```

## Rules

- documentation/repository-only changes do not require a template version bump;
- any functional change to an item, trigger, macro, or collector must be recorded in `CHANGELOG.md`;
- maintained exports must use the same `vendor.version` when they represent the same functional release;
- a serialization-only refresh for a newer Zabbix build should not invent a new functional version unnecessarily;
- release tags use the `v` prefix.

## Release workflow

The `.github/workflows/release.yml` workflow is triggered by `v*` tags and checks that the tag without the `v` prefix matches the contents of `VERSION`.

Before creating a tag:

```sh
python tools/validate_templates.py
pytest -q
```

When the version is ready:

```text
VERSION = X.Y.Z
vendor.version = X.Y.Z in every maintained export
tag = vX.Y.Z
```

The workflow validates the project, builds a ZIP containing scripts, templates, documentation, and metadata, and creates the GitHub Release.
