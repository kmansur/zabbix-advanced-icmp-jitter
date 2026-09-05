# Versionamento

## Versão atual

O projeto mantém atualmente a versão histórica:

```text
1.0-10
```

Ela aparece nos exports Zabbix como:

```yaml
vendor:
  name: Net Tech
  version: 1.0-10
```

O arquivo `VERSION` na raiz deve possuir o mesmo valor.

Essa versão não foi alterada durante a reorganização do repositório porque não houve mudança funcional no template e os exports 7.0/8.0 já haviam sido validados com esse número.

## Transição para Semantic Versioning

A próxima release **funcional** deve iniciar o padrão `MAJOR.MINOR.PATCH`.

Exemplos:

- `1.0.11`: correção compatível com o comportamento atual;
- `1.1.0`: nova funcionalidade, item, métrica ou trigger compatível;
- `2.0.0`: alteração incompatível de key, macro, instalação ou comportamento.

Após a transição, o padrão será:

```text
VERSION                1.1.0
vendor.version          1.1.0
Git tag                 v1.1.0
GitHub Release          v1.1.0
```

## Regras

- alterações somente de documentação/repositório não exigem bump do template;
- qualquer mudança funcional em item, trigger, macro ou coletor deve ser registrada no `CHANGELOG.md`;
- os exports mantidos devem usar a mesma `vendor.version` quando representam a mesma release funcional;
- uma atualização específica apenas de serialização para uma nova build do Zabbix não deve inventar uma nova versão funcional sem necessidade;
- tags de release usam prefixo `v`.

## Workflow de release

O workflow `.github/workflows/release.yml` é disparado por tags `v*` e verifica se a tag sem o prefixo `v` corresponde ao conteúdo de `VERSION`.

Antes de criar uma tag:

```sh
python tools/validate_templates.py
pytest -q
```

Depois, quando a versão estiver pronta:

```text
VERSION = X.Y.Z
vendor.version = X.Y.Z em todos os exports mantidos
tag = vX.Y.Z
```

O workflow valida o projeto, monta um ZIP com scripts, templates, documentação e metadados, e cria a GitHub Release.
