# Métricas e dashboard

## Arquitetura de coleta

O template executa um único lote ICMP por atualização. O item mestre chama o coletor Python e recebe JSON; todos os demais itens usam o mesmo payload por meio de itens dependentes e JSONPath.

Isso evita múltiplos comandos de ping para o mesmo host e mantém todas as métricas calculadas sobre a mesma amostra.

## Itens

| Item | Key | Tipo |
| --- | --- | --- |
| Advanced ICMP: raw JSON results | `advanced_icmp_ping.py[...]` | External |
| Advanced ICMP: average response time | `advanced.ping.avg` | Dependente |
| Advanced ICMP: minimum response time | `advanced.ping.min` | Dependente |
| Advanced ICMP: maximum response time | `advanced.ping.max` | Dependente |
| Advanced ICMP: packet loss | `advanced.ping.loss` | Dependente |
| Advanced ICMP: packets sent | `advanced.ping.xmt` | Dependente |
| Advanced ICMP: packets received | `advanced.ping.rcv` | Dependente |
| Advanced ICMP: jitter | `advanced.ping.jitter` | Dependente |
| Advanced ICMP: RTT standard deviation | `advanced.ping.stddev` | Dependente |
| Advanced ICMP: collector error | `advanced.ping.error` | Dependente |

Os nomes dos itens permanecem em inglês para manter consistência com os exports e evitar alterações cosméticas que possam confundir ambientes já existentes.

## Cálculo do jitter

O jitter é a média da diferença absoluta entre respostas RTT consecutivas recebidas:

```text
jitter = média(abs(rtt_atual - rtt_anterior))
```

Exemplo:

```text
RTTs:       10.0, 13.0, 11.0, 20.0
Diferenças:  3.0,  2.0,  9.0
Jitter:      4.667 ms
```

Pacotes perdidos não entram no cálculo de RTT porque não possuem tempo de resposta. Eles continuam contabilizados em `xmt`, `rcv` e `loss`.

## Desvio padrão do RTT

O coletor calcula o desvio padrão populacional das respostas recebidas.

Interpretação prática:

- `stddev` baixo: latência concentrada e estável;
- `stddev` alto: grande dispersão das amostras, mesmo que a média ainda pareça aceitável.

Jitter e desvio padrão são complementares:

- `jitter` mede variação entre respostas consecutivas;
- `stddev` mede a dispersão geral do conjunto de RTTs.

## JSON bruto

O item mestre mantém o JSON completo para troubleshooting. Exemplo:

```json
{"error":"","xmt":20,"rcv":20,"loss":0.0,"min":10.1,"avg":12.65,"max":16.3,"jitter":1.678,"stddev":1.887,"rtts":[11.9,11.3],"target":"8.8.8.8"}
```

O array `rtts` facilita a análise das amostras individuais quando necessário.

## Dashboard

O template inclui o dashboard:

```text
Advanced ICMP
```

com o gráfico:

```text
Advanced ICMP: latency, loss, jitter and deviation
```

O JSON bruto não é exibido no dashboard padrão, para manter a visualização focada nas métricas operacionais.

O gráfico clássico utiliza limite superior de `200` para facilitar comparação entre hosts e evitar que picos comuns de WAN sejam cortados.

![Exemplo do gráfico Advanced ICMP](../images/advanced-icmp-ping.png)
