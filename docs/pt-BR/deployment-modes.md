# Modos de implantação

[English](../en/deployment-modes.md) | **Português (Brasil)**

O projeto oferece dois modos complementares de monitoramento.

## Advanced ICMP Ping — padrão nativo e escalável

Use `advanced-icmp-ping.yaml` para aplicação ampla. Ele usa checks `SIMPLE` nativos do Zabbix:

- `icmpping` para disponibilidade;
- `icmppingloss` para perda de pacotes;
- `icmppingsec` em modo `avg` para RTT médio.

Os três são executados pelos processos ICMP pinger do Zabbix server/proxy. Alvos com parâmetros idênticos podem ser agrupados e verificados pelo `fping` em paralelo, evitando um processo Python por host monitorado. O intervalo padrão é de um minuto, com indisponibilidade curta em aproximadamente 3 minutos e prolongada em aproximadamente 30 minutos.

## Advanced ICMP Ping with Jitter — estatística avançada seletiva

Use `advanced-icmp-ping-with-jitter.yaml` onde forem necessárias amostras individuais de RTT, jitter, desvio padrão populacional ou min/max do mesmo lote de pacotes. Seu item mestre é um check `EXTERNAL`: o Zabbix server/proxy inicia o coletor Python, que inicia o `fping`, para cada host vinculado e ciclo de coleta.

Alvos típicos incluem gateways WAN, enlaces entre sites, firewalls, roteadores de borda, caminhos de voz/vídeo e enlaces em troubleshooting.

Não vincule os dois templates ao mesmo host, a menos que queira intencionalmente o baseline nativo e também a carga estatística externa adicional.
