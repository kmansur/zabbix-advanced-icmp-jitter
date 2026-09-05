# Advanced ICMP Ping with Jitter — Documentação em Português (Brasil)

Template para Zabbix 7.0 destinado ao monitoramento avançado de ICMP, incluindo latência, perda de pacotes, jitter e desvio padrão de RTT usando `fping` e um script externo em Python.

O projeto é indicado para monitoramento de dispositivos de rede, links WAN, servidores, gateways e qualquer host em que disponibilidade ICMP e estabilidade de latência sejam importantes.

## Compatibilidade

Esta versão do template foi exportada para:

- Zabbix 7.0.

Arquivo do template:

```text
templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml
```

O coletor Python é compartilhado pelo projeto:

```text
advanced_icmp_ping.py
```

## O que o template monitora

O template executa um único lote de testes ICMP e calcula todas as métricas a partir da mesma amostra. Isso evita múltiplas execuções de ping para o mesmo host e mantém as métricas consistentes entre si.

Métricas coletadas:

- tempo médio de resposta ICMP;
- tempo mínimo de resposta ICMP;
- tempo máximo de resposta ICMP;
- perda de pacotes em percentual;
- quantidade de pacotes transmitidos;
- quantidade de pacotes recebidos;
- jitter ICMP;
- desvio padrão do RTT;
- estado de erro do coletor;
- resultado JSON bruto para diagnóstico.

## Como funciona

O template possui um item mestre do tipo `External check`:

```text
advanced_icmp_ping.py["{HOST.CONN}","{$ADV_FPING_POOL_COUNT}","{$ADV_FPING_INTERVAL_MS}","{$ADV_FPING_TIMEOUT_MS}"]
```

O script executa o `fping` aproximadamente desta forma:

```sh
fping -q -C <quantidade> -p <intervalo_ms> -t <timeout_ms> <host>
```

A opção `-C` do `fping` retorna um RTT individual para cada pacote transmitido. O script interpreta essas amostras e devolve um JSON ao Zabbix.

Os demais itens do template são itens dependentes que utilizam pré-processamento JSONPath.

Esse desenho oferece duas vantagens principais:

- apenas um lote ICMP por intervalo de coleta;
- latência, perda, jitter e desvio padrão são calculados sobre a mesma amostra de pacotes.

## Cálculo do jitter

O jitter é calculado como a média da diferença absoluta entre amostras de RTT consecutivas recebidas:

```text
jitter = média(abs(rtt_atual - rtt_anterior))
```

Exemplo:

```text
RTTs:       10.0, 13.0, 11.0, 20.0
Diferenças:  3.0,  2.0,  9.0
Jitter:      4.667 ms
```

Pacotes perdidos não participam do cálculo do RTT, pois não possuem tempo de resposta. Eles continuam sendo contabilizados nas métricas de pacotes enviados, recebidos e perda.

## Desvio padrão do RTT

O desvio padrão indica o quanto os tempos de resposta recebidos estão dispersos em relação à média.

Interpretação prática:

- desvio padrão baixo: latência estável;
- desvio padrão alto: latência irregular, mesmo quando a média parece aceitável.

Jitter e desvio padrão são métricas complementares:

- `jitter` mede a variação entre pacotes consecutivos;
- `stddev` mede a dispersão geral do RTT dentro do lote coletado.

## Requisitos

- Zabbix Server ou Zabbix Proxy 7.0;
- Python 3 disponível no servidor/proxy que executará o external check;
- `fping` instalado;
- diretório `ExternalScripts` configurado ou utilizando o caminho padrão da instalação;
- usuário do processo Zabbix com permissão para executar `fping` e o script Python.

## Instalação das dependências

### Debian / Ubuntu

```sh
apt update
apt install python3 fping
```

### RHEL / Rocky Linux / AlmaLinux

```sh
dnf install python3 fping
```

### FreeBSD

```sh
pkg install python3 fping
```

## Instalação do coletor

Copie o arquivo `advanced_icmp_ping.py` para o diretório de scripts externos do Zabbix.

Exemplo comum em Linux:

```sh
cp advanced_icmp_ping.py /usr/lib/zabbix/externalscripts/
chmod +x /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

Para verificar se existe uma configuração explícita de `ExternalScripts`:

```sh
grep -i '^ExternalScripts' /etc/zabbix/zabbix_server.conf
grep -i '^ExternalScripts' /etc/zabbix/zabbix_proxy.conf
```

Caminhos frequentemente utilizados:

```text
/usr/lib/zabbix/externalscripts
/usr/local/share/zabbix/externalscripts
```

## Teste manual do coletor

Sempre que possível, teste utilizando o mesmo usuário que executa o Zabbix:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Exemplo de saída válida:

```json
{"error":"","xmt":20,"rcv":20,"loss":0.0,"min":10.1,"avg":12.65,"max":16.3,"jitter":1.678,"stddev":1.887,"rtts":[11.9,11.3],"target":"8.8.8.8"}
```

Quando existe uma falha de coleta, o script ainda deve retornar JSON válido. Exemplo:

```json
{"error":"fping command not found","xmt":0,"rcv":0,"loss":100,"min":0,"avg":0,"max":0,"jitter":0,"stddev":0,"rtts":[]}
```

O template possui um trigger específico para sinalizar erros do coletor.

## Importação do template no Zabbix 7.0

No frontend do Zabbix:

1. acesse `Data collection` > `Templates`;
2. clique em `Import`;
3. selecione:

```text
templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml
```

4. revise as regras de importação;
5. conclua a importação;
6. vincule o template aos hosts desejados.

O alvo do teste é obtido por meio da macro interna:

```text
{HOST.CONN}
```

Portanto, confirme que a interface do host está configurada para utilizar o endereço IP ou DNS esperado.

## Formatos de destino suportados

O coletor aceita destinos compreendidos pelo `fping`, incluindo:

- IPv4, por exemplo `8.8.8.8`;
- nomes DNS, por exemplo `example.com`;
- IPv6, por exemplo `2001:4860:4860::8888`, desde que o sistema possua conectividade IPv6 e uma versão do `fping` com suporte adequado.

Teste manual IPv6:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 2001:4860:4860::8888 20 100 1000
```

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

A configuração padrão utiliza 20 pacotes espaçados em 100 ms, produzindo uma janela aproximada de 2 segundos por lote.

## Recomendações de ajuste

### Monitoramento WAN geral

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=100
{$ADV_FPING_TIMEOUT_MS}=1000
{$ADV_ICMP_JITTER_WARN}=20
```

### LAN ou datacenter de baixa latência

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_ICMP_JITTER_WARN}=5
{$ADV_ICMP_STDDEV_WARN}=10
```

### Links de Internet com latência mais elevada

```text
{$ADV_FPING_POOL_COUNT}=20
{$ADV_FPING_INTERVAL_MS}=100
{$ADV_ICMP_JITTER_WARN}=30
{$ADV_ICMP_STDDEV_WARN}=50
```

### Links sensíveis a voz ou vídeo

```text
{$ADV_FPING_POOL_COUNT}=30
{$ADV_FPING_INTERVAL_MS}=50
{$ADV_ICMP_JITTER_WARN}=20
{$ADV_ICMP_STDDEV_WARN}=30
```

A duração aproximada do lote pode ser estimada por:

```text
duração ~= quantidade_de_pacotes * intervalo_ms
```

Exemplos:

```text
20 pacotes * 100 ms = aproximadamente 2 segundos
30 pacotes * 50 ms  = aproximadamente 1,5 segundo
```

## Itens do template

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

Os nomes dos itens permanecem em inglês para manter consistência com o template exportado e evitar mudanças cosméticas desnecessárias em ambientes já existentes.

## Triggers

Ativados por padrão:

- `Advanced ICMP: Unavailable by ICMP ping`;
- `Advanced ICMP: Long unavailable by ICMP ping`;
- `Advanced ICMP: High packet loss`;
- `Advanced ICMP: High response time`;
- `Advanced ICMP: High jitter`;
- `Advanced ICMP: High time differences (Min/Max)`;
- `Advanced ICMP: Collector error`.

Desativado por padrão:

- `Advanced ICMP: High RTT standard deviation`.

### Indisponibilidade curta

O trigger de indisponibilidade curta entra em estado de problema quando nenhuma resposta ICMP é recebida durante os últimos 3 lotes coletados:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#3)=0
```

### Indisponibilidade prolongada

O trigger de indisponibilidade prolongada funciona como uma escalada e exige 30 lotes consecutivos sem resposta:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#30)=0
```

O trigger curto possui dependência do trigger de indisponibilidade prolongada para evitar dois problemas simultâneos representando a mesma falha.

A recuperação é automática quando novas respostas ICMP voltam a ser recebidas.

## Dashboard e gráfico

O template inclui um dashboard chamado:

```text
Advanced ICMP
```

O gráfico principal é:

```text
Advanced ICMP: latency, loss, jitter and deviation
```

O item contendo o JSON bruto não é exibido no dashboard por padrão. Ele permanece disponível no histórico para diagnóstico.

O gráfico clássico utiliza faixa fixa de `0-200` no eixo Y para manter comparabilidade visual entre hosts e reduzir distorções causadas por picos comuns de latência WAN.

Imagem de exemplo:

![Exemplo do gráfico Advanced ICMP](../../advanced_icmp_ping.png)

## Troubleshooting

### O Zabbix informa que o script não foi encontrado

Confira o diretório e as permissões:

```sh
ls -l /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

O arquivo precisa estar acessível e executável pelo usuário do Zabbix.

### Erro `fping command not found`

Confira se o `fping` está instalado e disponível no ambiente do usuário Zabbix:

```sh
which fping
sudo -u zabbix fping -v
```

### Erro `unable to parse fping output`

Execute o coletor manualmente:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Teste também diretamente o `fping`:

```sh
sudo -u zabbix fping -q -C 5 -p 100 -t 1000 8.8.8.8
```

### Todos os pacotes aparecem como perdidos

Verifique:

- rota até o destino;
- políticas de firewall;
- bloqueio ou limitação de ICMP;
- conectividade IPv4/IPv6 conforme o endereço utilizado.

Alguns equipamentos podem limitar ICMP mesmo quando serviços TCP/UDP continuam respondendo normalmente.

### A coleta está demorando demais

Reduza a quantidade de pacotes ou o intervalo:

```text
{$ADV_FPING_POOL_COUNT}=10
{$ADV_FPING_INTERVAL_MS}=100
```

Evite intervalos extremamente baixos em servidores Zabbix que monitoram grande quantidade de hosts.

### O jitter apresenta muita variação

Aumente a quantidade de amostras:

```text
{$ADV_FPING_POOL_COUNT}=30
```

Para alertas de jitter, prefira janelas de média. O template já utiliza média de 5 minutos no trigger padrão de jitter.

## Licença e atribuição

Este projeto é baseado no `AdvancedPING`, de Dusan Priechodsky:

```text
https://github.com/priechodsky/AdvancedPING
```

O projeto original é distribuído sob GNU General Public License v3.0. Esta versão modificada também é distribuída sob GPL-3.0.

Modificações mantidas por Karim Mansur / Net Tech.

Consulte o arquivo `LICENSE` na raiz do repositório para o texto completo da licença.

## Versionamento atual

O template Zabbix 7.0 possui atualmente:

```yaml
vendor:
  name: 'Net Tech'
  version: 1.0-10
```

O coletor Python possui versionamento próprio no cabeçalho do script.

Enquanto o projeto estiver nesta linha de compatibilidade, alterações específicas do template Zabbix 7.0 devem permanecer em:

```text
templates/zabbix-7.0/
```

Quando existir uma versão específica para outra linha principal do Zabbix, ela deverá receber seu próprio diretório, por exemplo:

```text
templates/zabbix-8.0/
```

Isso evita misturar exports de versões diferentes e torna a compatibilidade explícita na estrutura do repositório.
