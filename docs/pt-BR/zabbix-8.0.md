# Compatibilidade com Zabbix 8.0

O projeto possui um export específico para Zabbix 8.0 em:

```text
templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml
```

Esse arquivo foi obtido a partir de um template importado com sucesso no Zabbix 8.0 e posteriormente exportado pelo próprio frontend.

## Validação

A versão 8.0 foi comparada com o template Zabbix 7.0 do projeto. A lógica de monitoramento foi preservada:

- mesmo UUID e nome do template;
- mesmo vendor e versão do template (`Net Tech`, `1.0-10`);
- mesmos 10 itens e respectivas keys;
- mesmas 8 macros e valores padrão;
- mesmas expressões de triggers e dependências;
- mesmo dashboard;
- mesmo gráfico e séries;
- mesmo script externo `advanced_icmp_ping.py`.

As diferenças observadas são de serialização do export do Zabbix 8.0 e não alteram a lógica do template. Entre elas:

- `zabbix_export.version` passa de `7.0` para `8.0`;
- alguns campos com valores padrão deixam de ser exportados explicitamente;
- a ordem de itens e macros pode ser normalizada pelo Zabbix;
- o dashboard passa a registrar explicitamente `auto_start: 'YES'`;
- o gráfico mantém o limite superior de `200`, enquanto alguns valores padrão do eixo deixam de aparecer explicitamente no YAML.

## Importação

No frontend do Zabbix 8.0:

1. acesse **Data collection > Templates**;
2. clique em **Import**;
3. selecione `templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml`;
4. revise as alterações apresentadas pelo frontend;
5. conclua a importação;
6. vincule o template aos hosts desejados.

O coletor Python é o mesmo utilizado pela versão 7.0 e deve estar instalado no diretório `ExternalScripts` do Zabbix Server ou Proxy.

## Referência oficial

A documentação oficial do Zabbix 8.0 define `zabbix_export.version: '8.0'` para exports YAML e mantém suporte a templates com itens dependentes, pré-processamento, triggers, dashboards e gráficos. O export desta versão segue essa estrutura.
