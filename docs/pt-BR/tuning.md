# Ajustes e tuning

[English](../en/tuning.md) | **Português (Brasil)**

Os valores ideais dependem da característica do enlace, quantidade de hosts monitorados e sensibilidade desejada para alertas.

## Monitoramento WAN geral

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=250
{$ADV_FPING_TIMEOUT_MS}=250
{$ADV_ICMP_JITTER_WARN}=20
```

É o perfil padrão do projeto e oferece boa relação entre duração do lote e quantidade de amostras.

## LAN ou datacenter de baixa latência

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_FPING_TIMEOUT_MS}=50
{$ADV_ICMP_JITTER_WARN}=5
{$ADV_ICMP_STDDEV_WARN}=10
```

Use limites menores somente quando a rede realmente tiver latência e variação muito baixas.

## Internet ou caminhos com latência mais elevada

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=100
{$ADV_FPING_TIMEOUT_MS}=100
{$ADV_ICMP_JITTER_WARN}=30
{$ADV_ICMP_STDDEV_WARN}=50
```

## Voz, vídeo ou aplicações sensíveis a variação

```text
{$ADV_FPING_POOL_COUNT}=30
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_FPING_TIMEOUT_MS}=50
{$ADV_ICMP_JITTER_WARN}=20
{$ADV_ICMP_STDDEV_WARN}=30
```

Aumentar o número de pacotes melhora a quantidade de amostras disponíveis para jitter e desvio padrão, mas também aumenta a duração e o custo da coleta.

## Duração aproximada

```text
duração ~= quantidade_de_pacotes * intervalo_ms
```

Exemplos:

```text
20 pacotes * 100 ms = aproximadamente 2 segundos
30 pacotes * 50 ms  = aproximadamente 1,5 segundo
```

O timeout real do processo Python inclui uma margem adicional sobre o tempo esperado do `fping`.

## Escala do ambiente

O template é híbrido e único. Disponibilidade, perda e RTT médio usam o ICMP pinger nativo a cada `1m`; jitter, desvio padrão e min/max do mesmo lote usam o coletor externo em `{$ADV_ICMP_STATS_INTERVAL}` (padrão `5m`).

Para aumentar a escala sem perder sensibilidade de estado:

- mantenha o caminho nativo em `1m`;
- aumente `{$ADV_ICMP_STATS_INTERVAL}` para `10m` ou `15m` quando a estatística avançada puder ser menos frequente;
- distribua hosts entre proxies quando necessário;
- acompanhe utilização de ICMP pingers e pollers de external checks;
- aumente `POOL_COUNT` somente quando o ganho estatístico justificar o custo.

## Ajuste de triggers

Antes de reduzir thresholds, observe o comportamento real da rede por alguns dias. Em particular:

- `{$ADV_ICMP_JITTER_WARN}` deve refletir a variação normal do caminho;
- `{$ADV_ICMP_RESPONSE_TIME_WARN}` deve considerar distância e tipo do enlace;
- `{$ADV_ICMP_LOSS_WARN}` deve separar perda transitória de degradação operacional;
- `{$ADV_ICMP_STDDEV_WARN}` é mais útil em enlaces onde estabilidade importa tanto quanto a média.

O trigger de desvio padrão fica desabilitado por padrão para evitar ruído em ambientes onde essa métrica é apenas informativa.

## Retenção

Os itens numéricos do template usam por padrão 30 dias de histórico e o JSON bruto do coletor avançado mantém 1 hora. Ajuste a retenção conforme a escala do banco e a necessidade de análise forense.
