# Configuração e macros

[English](../en/configuration.md) | **Português (Brasil)**

## Destino monitorado

O item mestre usa:

```text
{HOST.CONN}
```

Portanto, o destino efetivo depende da interface selecionada no host do Zabbix e da opção de conexão por IP ou DNS.

Formatos suportados pelo coletor, desde que aceitos pelo `fping` instalado:

- IPv4, por exemplo `8.8.8.8`;
- DNS, por exemplo `example.com`;
- IPv6, por exemplo `2001:4860:4860::8888`.

## Item mestre

A key usada pelos exports mantidos é:

```text
advanced_icmp_ping.py["{HOST.CONN}","{$ADV_FPING_POOL_COUNT}","{$ADV_FPING_INTERVAL_MS}","{$ADV_FPING_TIMEOUT_MS}"]
```

Os parâmetros são posicionais porque o Zabbix passa as macros diretamente para o script externo.

## Macros padrão

| Macro | Padrão | Finalidade |
| --- | ---: | --- |
| `{$ADV_FPING_POOL_COUNT}` | `20` | Quantidade de sondagens ICMP por lote. |
| `{$ADV_FPING_INTERVAL_MS}` | `100` | Intervalo entre sondagens, em milissegundos. |
| `{$ADV_FPING_TIMEOUT_MS}` | `1000` | Timeout de cada sondagem, em milissegundos. |
| `{$ADV_ICMP_LOSS_WARN}` | `20` | Limite de alerta de perda de pacotes, em %. |
| `{$ADV_ICMP_JITTER_WARN}` | `20` | Limite de alerta de jitter, em ms. |
| `{$ADV_ICMP_RESPONSE_TIME_WARN}` | `200` | Limite de alerta para latência média, em ms. |
| `{$ADV_ICMP_MAX_TIME_MULTIPLE}` | `30` | Limite para a relação entre RTT máximo e mínimo. |
| `{$ADV_ICMP_STDDEV_WARN}` | `30` | Limite de alerta para desvio padrão do RTT, em ms. |

## Limites de segurança do coletor

O coletor valida e limita os valores recebidos para evitar parâmetros acidentais muito baixos, negativos ou excessivamente altos:

- quantidade de pacotes: mínimo `2`, máximo `100`;
- intervalo: mínimo `20 ms`, máximo `60000 ms`;
- timeout: mínimo `50 ms`, máximo `60000 ms`.

Valores inválidos usam os padrões internos do coletor.

## Janela de medição

Uma aproximação simples da duração do lote é:

```text
duração ~= quantidade_de_pacotes * intervalo_ms
```

Exemplo padrão:

```text
20 pacotes * 100 ms = aproximadamente 2 segundos
```

O timeout do processo Python é calculado com margem adicional para evitar que um `fping` travado ocupe indefinidamente um poller do Zabbix.

## Escolha do export

Use sempre o diretório correspondente à versão principal/secundária do Zabbix:

```text
templates/zabbix-7.0/
templates/zabbix-8.0/
```

O validador do repositório impede que um YAML declare uma versão diferente da versão indicada pelo diretório.
