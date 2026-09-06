# Arquitetura de implantação

[English](../en/deployment-modes.md) | **Português (Brasil)**

O projeto usa **um único template híbrido**: `Advanced ICMP Ping with Jitter`.

## Caminho principal — nativo e escalável

A cada minuto o Zabbix usa seus checks `SIMPLE` nativos:

- `icmpping` para disponibilidade;
- `icmppingloss` para perda de pacotes;
- `icmppingsec` em modo `avg` para RTT médio.

Esses checks são processados pelos ICMP pingers do Zabbix server/proxy. Destinos com parâmetros compatíveis podem ser agrupados pelo `fping`, evitando um processo Python por host no caminho de monitoramento que determina estado, perda e latência média.

## Estatística avançada — integrada ao mesmo template

O mesmo template mantém um único item `EXTERNAL`, mas em frequência menor, controlada por `{$ADV_ICMP_STATS_INTERVAL}` (padrão `5m`). Ele existe apenas para métricas que o ICMP nativo não fornece a partir dos RTTs individuais do mesmo lote:

- jitter pacote a pacote;
- desvio padrão do RTT;
- RTT mínimo e máximo do mesmo lote de amostras.

Se o coletor avançado falhar, o item `Collector error` alerta, porém disponibilidade, perda e RTT médio continuam sendo medidos pelo ICMP nativo e não dependem do Python.

## Escala

Para ambientes maiores, mantenha o core em `1m` e aumente apenas `{$ADV_ICMP_STATS_INTERVAL}` para `10m` ou `15m` se a estatística avançada não precisar de alta frequência. Assim, a sensibilidade do estado do dispositivo permanece em aproximadamente 3 minutos, enquanto a carga de external checks pode ser reduzida de forma independente.
