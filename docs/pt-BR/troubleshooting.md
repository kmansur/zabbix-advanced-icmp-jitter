# Troubleshooting

[English](../en/troubleshooting.md) | **Português (Brasil)**

## O Zabbix informa que o script não foi encontrado

Confirme o caminho e as permissões:

```sh
ls -l /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
```

O arquivo precisa estar acessível e executável pelo usuário do processo Zabbix.

No repositório, o arquivo de origem fica em:

```text
scripts/advanced_icmp_ping.py
```

## `fping command not found`

Confira se o `fping` está instalado e disponível para o usuário Zabbix:

```sh
which fping
sudo -u zabbix fping -v
```

## `unable to parse fping output`

Execute o coletor manualmente:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 100 1000
```

Teste também o formato retornado pelo próprio `fping`:

```sh
sudo -u zabbix fping -q -C 5 -p 100 -t 1000 8.8.8.8
```

O parser espera linhas de amostras com números de RTT ou `-` para pacotes perdidos.

## Todos os pacotes aparecem como perdidos

Verifique:

- rota até o destino;
- políticas de firewall;
- bloqueio ou limitação de ICMP;
- conectividade IPv4/IPv6 conforme o destino;
- permissões/capabilities do `fping` no sistema operacional.

Alguns equipamentos limitam ICMP mesmo quando serviços TCP/UDP continuam respondendo.

## A coleta está demorando demais

Reduza a quantidade de pacotes ou o intervalo:

```text
{$ADV_FPING_POOL_COUNT}=10
{$ADV_FPING_INTERVAL_MS}=100
```

Evite intervalos extremamente baixos em servidores Zabbix com muitos hosts.

## Jitter muito variável

Aumente a quantidade de amostras:

```text
{$ADV_FPING_POOL_COUNT}=30
```

O trigger padrão já usa média de 5 minutos para reduzir ruído de amostras isoladas.

## IPv6 não funciona

Teste o `fping` diretamente como usuário Zabbix e confirme conectividade IPv6:

```sh
sudo -u zabbix fping -q -C 5 -p 100 -t 1000 2001:4860:4860::8888
```

Depois teste o coletor:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 2001:4860:4860::8888 20 100 1000
```

O parser do projeto possui teste específico para endereços IPv6 com múltiplos `:`.

## Template não importa

Confirme se o YAML corresponde à versão do Zabbix:

```text
templates/zabbix-7.0/ -> zabbix_export.version: '7.0'
templates/zabbix-8.0/ -> zabbix_export.version: '8.0'
```

Em desenvolvimento, rode:

```sh
python tools/validate_templates.py
```

O export 8.0 atualmente mantido foi testado no **Zabbix 8.0 Beta 2**. Se uma nova Beta, RC ou release final rejeitar o arquivo, exporte novamente a partir dessa build e compare a estrutura antes de substituir o arquivo do projeto.

## Diagnóstico do JSON bruto

Abra o histórico do item mestre `Advanced ICMP: raw JSON results` para verificar:

- `error`;
- `xmt`;
- `rcv`;
- `loss`;
- `rtts`.

O campo `error` vazio indica que o coletor executou sem erro operacional detectado.
