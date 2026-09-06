# Histórico de alterações

[English](CHANGELOG.md) | **Português (Brasil)**

Todas as alterações relevantes do `Advanced ICMP Ping with Jitter` são documentadas aqui.

A versão do template é armazenada no export Zabbix em:

```yaml
vendor:
  name: 'Net Tech'
  version: x.y-z
```

## [Não lançado]

### Adicionado

- `VERSION` como fonte de referência no repositório para a versão funcional atual do template.
- Testes unitários e fixtures representativas de `fping` para IPv4, IPv6, perda de pacotes, perda total, saída malformada, estatísticas e execução do coletor.
- Validação semântica dos exports Zabbix versionados, incluindo correspondência entre diretório/versão do export e paridade entre versões de UUIDs, keys, macros, triggers, dashboards, gráficos e versão do vendor.
- CI para Python 3.9, 3.13 e 3.14 com compilação, Ruff, pytest e validação dos templates Zabbix.
- CodeQL, Dependabot, automação de release por tag, template de PR e formulários estruturados de issue.
- `SECURITY.md`, `CONTRIBUTING.md`, `NOTICE.md`, `.editorconfig`, `.gitattributes`, `.gitignore`, `pyproject.toml` e definições de dependências de desenvolvimento.
- Documentação completa e espelhada em inglês e Português do Brasil, incluindo instalação, configuração, métricas, triggers, tuning, troubleshooting, compatibilidade com Zabbix 8.0 e versionamento.
- `README.pt-BR.md`, `CONTRIBUTING.pt-BR.md`, `SECURITY.pt-BR.md`, `NOTICE.pt-BR.md` e `CHANGELOG.pt-BR.md`.

### Alterado

- Coletor de produção movido da raiz do repositório para `scripts/advanced_icmp_ping.py` sem alteração da lógica de monitoramento.
- Imagem de exemplo do gráfico movida para `docs/images/advanced-icmp-ping.png`.
- `README.md` raiz simplificado como landing page do projeto com compatibilidade, início rápido, desenvolvimento e links para documentação.
- Documentado que a versão atual `1.0-10` permanece inalterada para reorganizações apenas do repositório e que a próxima release funcional fará a transição para Semantic Versioning.
- Links de idioma padronizados para separar claramente inglês e Português do Brasil.

## [1.0-10] - 2026-05-11

### Alterado

- Habilitado o trigger de indisponibilidade ICMP prolongada como sinal de escalada.
- Renomeado `Advanced ICMP: Total unavailable by ICMP ping` para `Advanced ICMP: Long unavailable by ICMP ping` para maior clareza.
- Expressões de indisponibilidade alteradas de `last(...,#N)=0` para `max(...,#N)=0`, fazendo com que os triggers de indisponibilidade curta e prolongada avaliem janelas completas de coletas consecutivas sem resposta.
- Adicionada dependência do trigger `Advanced ICMP: Unavailable by ICMP ping` para `Advanced ICMP: Long unavailable by ICMP ping` a fim de evitar problemas visíveis duplicados durante indisponibilidades prolongadas.
- Documentado o comportamento de recuperação automática dos triggers de indisponibilidade.
- Versão do vendor do template atualizada para `1.0-10`.

## [1.0-9] - 2026-05-11

### Alterado

- Adicionado o prefixo `Advanced ICMP:` aos nomes visíveis dos itens para facilitar sua identificação em telas do Zabbix compartilhadas com o monitoramento ICMP padrão.
- Keys dos itens mantidas inalteradas para preservar histórico, referências de triggers e compatibilidade.
- Tabela de itens do README atualizada com os novos nomes visíveis.
- Versão do vendor do template atualizada para `1.0-9`.

## [1.0-8] - 2026-05-11

### Corrigido

- Corrigida a validação de importação do Zabbix para `yaxismin` e `yaxismax` do gráfico, exportando valores fixos de eixo como strings.
- Versão do vendor do template atualizada para `1.0-8`.

## [1.0-7] - 2026-05-11

### Alterado

- Adicionado o prefixo `Advanced ICMP:` aos nomes dos triggers para evitar confusão com triggers ICMP padrão em visualizações globais do Zabbix.
- Dashboard padrão renomeado para `Advanced ICMP`.
- Gráfico renomeado para `Advanced ICMP: latency, loss, jitter and deviation`.
- Faixa fixa do eixo Y do gráfico clássico definida como `0-200` para preservar comparação visual entre hosts e evitar corte de picos comuns de latência WAN.
- README atualizado com o comportamento do eixo fixo e exemplos dos triggers renomeados.
- Versão do vendor do template atualizada para `1.0-7`.

## [1.0-6] - 2026-05-01

### Alterado

- Removido do dashboard padrão o widget `itemhistory` do item mestre de JSON bruto.
- Aumentada a altura padrão do widget de gráfico para manter o dashboard focado nas métricas ICMP visuais.
- Mantido `ICMP raw JSON results` como item para troubleshooting.
- README atualizado para explicar por que o JSON bruto não é exibido no dashboard.
- Versão do vendor do template atualizada para `1.0-6`.

## [1.0-5] - 2026-05-01

### Corrigido

- Adicionado parsing seguro para IPv6 na saída de `fping -q -C`.
- Parser alterado para dividir a saída do `fping` pelo lado direito usando ` " : " `, evitando que endereços IPv6 sejam quebrados pelos dois-pontos internos.
- Adicionada proteção contra divisão por zero no trigger `High ICMP ping time differences (Min/Max)` quando a média do RTT mínimo é `0`.

### Alterado

- `advanced_icmp_ping.py` atualizado para a versão `1.0.5`.
- Suporte a destinos IPv4, DNS e IPv6 documentado no README.
- Adicionado exemplo de teste manual do coletor com IPv6.

## [1.0-4] - 2026-05-01

### Alterado

- Removidas linhas tracejadas do gráfico de latência.
- Item de tempo mínimo de resposta ICMP no gráfico alterado para `GRADIENT_LINE`.
- Latência máxima, jitter e desvio padrão mantidos como linhas regulares.
- Versão do vendor do template atualizada para `1.0-4`.

## [1.0-3] - 2026-05-01

### Alterado

- README ampliado com documentação detalhada de instalação, comportamento do coletor, tuning, itens, triggers, troubleshooting e licenciamento.
- `advanced_icmp_ping.py` atualizado para a versão `1.0.3`.
- Versão do vendor do template atualizada para `1.0-3`.

## [1.0-2] - 2026-05-01

### Adicionado

- Texto completo da GNU General Public License v3.0 como `LICENSE`.
- Atribuição ao projeto original `AdvancedPING` de Dusan Priechodsky.
- Avisos GPL-3.0 no README, descrição do template e cabeçalho do coletor Python.

### Alterado

- `advanced_icmp_ping.py` atualizado para a versão `1.0.2`.
- Versão do vendor do template atualizada para `1.0-2`.

## [1.0-1] - 2026-05-01

### Adicionado

- Item dependente `ICMP collector error`.
- Trigger `ICMP collector error`.
- Trigger `ICMP RTT standard deviation`, desabilitado por padrão.
- Macro `{$ADV_ICMP_STDDEV_WARN}`.
- README com notas de instalação, macros, triggers e coletor.

### Alterado

- Nomes dos itens atualizados para rótulos ICMP mais claros.
- Rótulos do gráfico e dashboard atualizados.
- Dependências do trigger de perda de pacotes alteradas para usar `{$ADV_ICMP_LOSS_WARN}` em vez de threshold fixo.
- Payloads JSON de sucesso do coletor atualizados para incluir `"error": ""`.
- `advanced_icmp_ping.py` atualizado para a versão `1.0.1`.
- Versão do vendor do template atualizada para `1.0-1`.

## [1.0-0] - 2026-05-01

### Adicionado

- Template inicial Zabbix 7.0: `Advanced ICMP Ping with Jitter`.
- Coletor Python: `advanced_icmp_ping.py`.
- Item mestre externo retornando JSON.
- Itens dependentes para:
  - RTT médio;
  - RTT mínimo;
  - RTT máximo;
  - perda de pacotes;
  - pacotes transmitidos;
  - pacotes recebidos;
  - jitter;
  - desvio padrão do RTT.
- Cálculo de jitter baseado na média da diferença absoluta entre amostras RTT consecutivas recebidas.
- Macros padrão do coletor:
  - `{$ADV_FPING_POOL_COUNT}=20`
  - `{$ADV_FPING_INTERVAL_MS}=100`
  - `{$ADV_FPING_TIMEOUT_MS}=1000`
- Macros padrão de alerta:
  - `{$ADV_ICMP_LOSS_WARN}=20`
  - `{$ADV_ICMP_JITTER_WARN}=20`
  - `{$ADV_ICMP_RESPONSE_TIME_WARN}=200`
  - `{$ADV_ICMP_MAX_TIME_MULTIPLE}=30`
- Dashboard e gráfico para latência, perda, jitter e desvio.

## Manutenção do repositório

### 2026-05-01

- Removido o helper shell legado e não utilizado `Advanced_ping.sh`.
- Diretório do projeto renomeado de `Adcanced ICMP Ping with Jitter` para `Advanced ICMP Ping with Jitter`.
- Adicionadas entradas `.gitignore` para cache Python:
  - `__pycache__/`
  - `*.pyc`
