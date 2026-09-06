# Triggers

[English](../en/triggers.md) | **Português (Brasil)**

## Ativados por padrão

- `Advanced ICMP: Unavailable by ICMP ping`;
- `Advanced ICMP: Long unavailable by ICMP ping`;
- `Advanced ICMP: High packet loss`;
- `Advanced ICMP: High response time`;
- `Advanced ICMP: High jitter`;
- `Advanced ICMP: High time differences (Min/Max)`;
- `Advanced ICMP: Collector error`.

## Desativado por padrão

- `Advanced ICMP: High RTT standard deviation`.

O trigger de desvio padrão fica desativado por padrão porque nem toda rede precisa alertar por dispersão. Ele pode ser habilitado em links sensíveis à estabilidade de latência.

## Indisponibilidade curta

O problema ocorre quando nenhuma resposta ICMP é recebida durante os últimos 3 lotes. Com o intervalo explícito de `1m` no item mestre, isso representa aproximadamente 3 minutos:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#3)=0
```

Prioridade padrão: `AVERAGE`.

## Indisponibilidade prolongada

A escalada de indisponibilidade exige 30 lotes consecutivos sem resposta. Com o intervalo explícito de `1m` no item mestre, isso representa aproximadamente 30 minutos:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#30)=0
```

Prioridade padrão: `HIGH`.

O trigger curto depende do trigger prolongado. Quando a indisponibilidade evolui para a condição longa, essa dependência evita dois problemas visíveis representando a mesma falha.

Ambos recuperam automaticamente quando a expressão volta a ser falsa e novas respostas aparecem dentro da janela avaliada.

## Perda de pacotes

```text
min(/Advanced ICMP Ping with Jitter/advanced.ping.loss,#2)>{$ADV_ICMP_LOSS_WARN} and min(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#2)>0
```

O limite é controlado por `{$ADV_ICMP_LOSS_WARN}`. O trigger representa degradação de conectividade somente quando os dois lotes avaliados ainda recebem pelo menos uma resposta ICMP. Perda total (`rcv=0`) é tratada pelos triggers de indisponibilidade.

## Latência média alta

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.avg,5m)>{$ADV_ICMP_RESPONSE_TIME_WARN}
```

O trigger depende de perda alta e indisponibilidade, reduzindo alertas derivados quando a causa principal é perda severa ou queda total.

## Jitter alto

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.jitter,5m)>{$ADV_ICMP_JITTER_WARN}
```

A média de 5 minutos reduz alertas provocados por uma única amostra isolada.

## Diferença alta entre RTT mínimo e máximo

A expressão compara a média do máximo com a média do mínimo e protege contra divisão por zero:

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.min,5m)>0 and avg(/Advanced ICMP Ping with Jitter/advanced.ping.max,5m)/avg(/Advanced ICMP Ping with Jitter/advanced.ping.min,5m)>{$ADV_ICMP_MAX_TIME_MULTIPLE}
```

## Desvio padrão alto

```text
avg(/Advanced ICMP Ping with Jitter/advanced.ping.stddev,5m)>{$ADV_ICMP_STDDEV_WARN}
```

Esse trigger é `DISABLED` no export padrão.

## Erro do coletor

```text
last(/Advanced ICMP Ping with Jitter/advanced.ping.error)<>""
```

Ele sinaliza problemas operacionais como `fping` ausente, timeout do comando ou saída não reconhecida pelo parser.
