# Advanced ICMP Ping with Jitter

[![CI](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/ci.yml/badge.svg)](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/security.yml/badge.svg)](https://github.com/kmansur/zabbix-advanced-icmp-jitter/actions/workflows/security.yml)

[English](README.md) | **Português (Brasil)**

Template Zabbix para monitoramento avançado de ICMP com latência, perda de pacotes, jitter e desvio padrão de RTT. Um único external check em Python executa `fping`, retorna JSON e alimenta itens dependentes do Zabbix usando o mesmo lote de sondagens.

## Compatibilidade

| Zabbix | Template | Status |
| --- | --- | --- |
| 7.0 | `templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml` | Suportado |
| 8.0 | `templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml` | Testado no **Zabbix 8.0 Beta 2**; será revalidado conforme novas Beta, RC e versão final forem testadas |

As notas de compatibilidade com Zabbix 8.0 estão em [docs/pt-BR/zabbix-8.0.md](docs/pt-BR/zabbix-8.0.md).

## Métricas

O template coleta um único lote ICMP e deriva:

- RTT médio, mínimo e máximo;
- perda de pacotes;
- contagem de pacotes enviados e recebidos;
- jitter baseado nas diferenças entre RTTs consecutivos recebidos;
- desvio padrão populacional do RTT;
- estado de erro do coletor;
- JSON bruto para troubleshooting.

## Estrutura do repositório

```text
.github/                 Workflows GitHub, Dependabot e templates de PR/issues
docs/
├── en/                  Documentação em inglês
├── images/              Imagens da documentação
└── pt-BR/               Documentação em Português do Brasil
scripts/                 Coletor externo usado em produção
templates/
├── zabbix-7.0/          Export Zabbix 7.0
└── zabbix-8.0/          Export Zabbix 8.0
tests/                   Testes unitários e fixtures do fping
tools/                   Ferramentas de validação do repositório e dos templates
```

## Início rápido

Instale as dependências do coletor no Zabbix Server ou Proxy.

Debian/Ubuntu:

```sh
apt update
apt install python3 fping
```

Instale o coletor no diretório de scripts externos do Zabbix:

```sh
cp scripts/advanced_icmp_ping.py /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
chmod +x /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

Teste como usuário Zabbix:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Depois importe o YAML correspondente à versão principal/secundária do Zabbix de destino.

## Documentação

Português (Brasil):

- [Visão geral](docs/pt-BR/README.md)
- [Instalação](docs/pt-BR/installation.md)
- [Configuração e macros](docs/pt-BR/configuration.md)
- [Métricas e dashboard](docs/pt-BR/metrics.md)
- [Triggers](docs/pt-BR/triggers.md)
- [Ajustes e tuning](docs/pt-BR/tuning.md)
- [Troubleshooting](docs/pt-BR/troubleshooting.md)
- [Compatibilidade com Zabbix 8.0](docs/pt-BR/zabbix-8.0.md)
- [Versionamento](docs/pt-BR/versioning.md)

A documentação em inglês está em [docs/en/](docs/en/README.md).

## Desenvolvimento

Instale as dependências de desenvolvimento:

```sh
python -m pip install -r requirements-dev.txt
```

Execute os mesmos checks usados pelo CI:

```sh
python -m compileall -q scripts tools tests
ruff check scripts tools tests
ruff format --check scripts tools tests
pytest -q
python tools/validate_templates.py
```

Consulte [CONTRIBUTING.pt-BR.md](CONTRIBUTING.pt-BR.md) para o fluxo de desenvolvimento e atualização dos exports Zabbix.

## Versionamento

A versão atual testada do template permanece `1.0-10` para preservar os exports existentes durante alterações somente de organização do repositório. A próxima release funcional fará a transição para Semantic Versioning (`MAJOR.MINOR.PATCH`).

O workflow de release exige que `VERSION`, `vendor.version` do Zabbix, a tag Git e a GitHub Release tenham a mesma versão.

## Licença e atribuição

Este projeto é baseado no [AdvancedPING](https://github.com/priechodsky/AdvancedPING) de Dusan Priechodsky e é distribuído sob GNU General Public License v3.0 (GPL-3.0).

Consulte [LICENSE](LICENSE) e [NOTICE.pt-BR.md](NOTICE.pt-BR.md).

Modificações mantidas por Karim Mansur / Net Tech.
