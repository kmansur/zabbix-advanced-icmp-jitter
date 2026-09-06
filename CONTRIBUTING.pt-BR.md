# Contribuindo

[English](CONTRIBUTING.md) | **Português (Brasil)**

Contribuições, relatos de bugs, melhorias de documentação e atualizações de compatibilidade são bem-vindos.

## Fluxo de desenvolvimento

1. Crie uma branch a partir de `main`.
2. Faça uma alteração focada.
3. Execute os comandos locais de validação.
4. Atualize a documentação quando comportamento, instalação ou compatibilidade mudarem.
5. Atualize `CHANGELOG.pt-BR.md` e `CHANGELOG.md` quando a mudança for visível ao usuário.
6. Abra um pull request.

Nomes de branch recomendados:

- `feature/<descricao>`
- `fix/<descricao>`
- `docs/<descricao>`
- `refactor/<descricao>`
- `ci/<descricao>`
- `chore/<descricao>`

## Mensagens de commit

Use Conventional Commits quando for prático:

- `feat:` nova funcionalidade;
- `fix:` correção de bug;
- `docs:` documentação;
- `refactor:` reorganização interna sem mudança de comportamento;
- `test:` testes e fixtures;
- `ci:` alterações de CI/CD;
- `chore:` manutenção do repositório.

## Validação local

Crie e ative um ambiente virtual se desejar e instale as ferramentas de desenvolvimento:

```sh
python -m pip install -r requirements-dev.txt
```

Execute:

```sh
python -m compileall -q scripts tools tests
ruff check scripts tools tests
ruff format --check scripts tools tests
pytest -q
python tools/validate_templates.py
```

O CI do pull request executa os mesmos checks.

## Regras para templates Zabbix

Exports específicos por versão ficam em:

```text
templates/zabbix-<major.minor>/
```

Exemplos:

```text
templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml
templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml
```

Ao adicionar ou atualizar um export Zabbix:

1. importe o template atualmente mantido na build Zabbix de destino;
2. confirme o funcionamento da coleta, itens dependentes, triggers, dashboard e gráfico;
3. exporte o template a partir desse frontend Zabbix;
4. armazene o export no diretório correspondente à versão;
5. execute `python tools/validate_templates.py`;
6. documente a build exata do Zabbix usada na validação.

O validador permite diferenças de serialização entre versões do Zabbix, mas exige alinhamento dos identificadores semânticos importantes, incluindo UUID do template, keys/UUIDs dos itens, macros, triggers, dashboards, gráficos e versão do vendor.

## Versionamento

A versão histórica atual do projeto é:

```text
1.0-10
```

Ela permanece inalterada durante reorganizações somente do repositório para evitar modificar desnecessariamente exports Zabbix já testados.

A próxima release **funcional** deve migrar para Semantic Versioning (`MAJOR.MINOR.PATCH`), por exemplo `1.0.11` ou `1.1.0`, conforme o escopo da mudança. A partir daí:

- `PATCH` = correções compatíveis;
- `MINOR` = novas funcionalidades ou métricas compatíveis;
- `MAJOR` = alterações incompatíveis de keys, macros, comportamento ou instalação.

Para uma release, estes valores precisam coincidir:

```text
VERSION
Zabbix vendor.version em todos os exports mantidos
Git tag (vX.Y.Z)
GitHub Release
```

## Alterações no coletor

O coletor de produção fica em:

```text
scripts/advanced_icmp_ping.py
```

Alterações no parser ou nas estatísticas devem incluir testes usando fixtures em `tests/fixtures/`. Evite utilizar alvos reais de rede nos testes unitários.

O coletor atualmente executa `fping` usando uma lista de argumentos, sem invocar um shell. Não substitua isso por construção de comando via shell sem uma razão forte e uma revisão específica de segurança.
