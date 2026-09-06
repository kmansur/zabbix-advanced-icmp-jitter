# Instalação

[English](../en/installation.md) | **Português (Brasil)**

## Requisitos

- Zabbix Server ou Zabbix Proxy compatível com um dos exports mantidos;
- Python 3.9 ou superior no servidor/proxy que executará o external check;
- `fping` instalado;
- diretório `ExternalScripts` configurado ou utilizando o caminho padrão da instalação;
- usuário do processo Zabbix com permissão para executar `fping` e o coletor.

O CI do projeto testa Python 3.9 e versões atuais do Python para evitar regressões no coletor mantido.

## Escolha do modo de implantação

Para a maioria dos hosts, importe e use `advanced-icmp-ping.yaml`. Ele precisa do `fping` no Zabbix server/proxy, mas não exige o coletor externo Python. Use `advanced-icmp-ping-with-jitter.yaml` somente nos alvos selecionados que precisam de jitter ou desvio padrão de RTT.

O template de jitter executa o item mestre `EXTERNAL` no Zabbix server/proxy, não no host monitorado. Portanto, cada host vinculado inicia uma execução Python/`fping` por ciclo de coleta.

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

No repositório, o coletor fica em:

```text
scripts/advanced_icmp_ping.py
```

Copie-o para o diretório de scripts externos do Zabbix. Exemplo comum em Linux:

```sh
cp scripts/advanced_icmp_ping.py /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py
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

Sempre que possível, teste com o mesmo usuário que executa o Zabbix:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 8.8.8.8 20 250 250
```

Exemplo de saída válida:

```json
{"error":"","xmt":20,"rcv":20,"loss":0.0,"min":10.1,"avg":12.65,"max":16.3,"jitter":1.678,"stddev":1.887,"rtts":[11.9,11.3],"target":"8.8.8.8"}
```

Se houver falha de coleta, o script continua retornando JSON válido para que os itens dependentes não recebam conteúdo malformado. Exemplo:

```json
{"error":"fping command not found","xmt":0,"rcv":0,"loss":100,"min":0,"avg":0,"max":0,"jitter":0,"stddev":0,"rtts":[]}
```

O candidato mantido da versão 1.1.0 exige `timeout <= interval` no modo count do `fping` e rejeita configurações cuja estimativa de execução ultrapasse o orçamento de segurança do coletor.

## Importação do template

No frontend do Zabbix:

1. acesse `Data collection` > `Templates`;
2. clique em `Import`;
3. escolha o arquivo correspondente à versão do Zabbix;
4. revise as alterações apresentadas pelo frontend;
5. conclua a importação;
6. vincule o template aos hosts desejados.

Arquivos mantidos:

```text
templates/zabbix-7.0/advanced-icmp-ping-with-jitter.yaml
templates/zabbix-8.0/advanced-icmp-ping-with-jitter.yaml
```

O export 8.0 foi testado no **Zabbix 8.0 Beta 2** e será revalidado conforme novas builds forem testadas.

### Migração a partir do AdvancedPING legado

Se o host utilizava anteriormente o template AdvancedPING original ou alguma derivação antiga, consulte o [guia de atualização do AdvancedPING legado](legacy-advancedping-upgrade.md) antes de remover ou vincular templates. Em especial, no Zabbix a opção **Unlink** preserva as entidades herdadas no host, enquanto **Unlink and clear** as remove; caso contrário, triggers locais legados podem coexistir com os triggers mantidos com prefixo `Advanced ICMP:`.

## Teste IPv6

O coletor aceita endereços compreendidos pelo `fping`. Para IPv6:

```sh
sudo -u zabbix /usr/lib/zabbix/externalscripts/advanced_icmp_ping.py 2001:4860:4860::8888 20 250 250
```

É necessário que o servidor/proxy tenha conectividade IPv6 e que o `fping` instalado ofereça suporte adequado.
