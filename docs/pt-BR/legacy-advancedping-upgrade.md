# Atualização a partir do AdvancedPING legado

[English](../en/legacy-advancedping-upgrade.md) | **Português (Brasil)**

Este guia é destinado a ambientes que utilizavam anteriormente o template original/legado `AdvancedPING` ou alguma derivação antiga e estão migrando para o **Advanced ICMP Ping with Jitter**.

O projeto atual mantém a atribuição histórica ao [AdvancedPING](https://github.com/priechodsky/AdvancedPING), mas os objetos do template, nomes de triggers, dependências, tags, valores padrão e regras de validação evoluíram.

## Por que objetos legados podem permanecer no host

O Zabbix oferece duas formas diferentes de remover um template vinculado a um host:

- **Unlink** remove a associação com o template, mas preserva no host entidades herdadas como items, triggers, gráficos, regras de descoberta de baixo nível e cenários web;
- **Unlink and clear** remove a associação e também remove as entidades herdadas.

Referências oficiais:

- [Zabbix 8.0 — Vincular/desvincular templates](https://www.zabbix.com/documentation/8.0/pt/manual/config/templates/linking)
- [Zabbix atual — Configurando um host](https://www.zabbix.com/documentation/current/pt/manual/config/hosts/host)

Se um template AdvancedPING legado foi removido utilizando apenas **Unlink**, objetos antigos podem permanecer como entidades locais do host mesmo depois que o novo template seja vinculado. Isso pode gerar triggers duplicados ou conflitantes.

## Assinaturas típicas do legado

Objetos legados podem utilizar as mesmas keys `advanced.ping.*`, mas com nomes ou expressões antigas. Exemplos encontrados em configurações antigas do AdvancedPING incluem:

```text
Unavailable by ICMP ping
High ICMP ping loss
```

Uma expressão antiga de disponibilidade pode aparecer como:

```text
last(/<host>/advanced.ping.rcv,#3)=0
```

O candidato mantido da versão 1.1.0 utiliza nomes e lógica como:

```text
Advanced ICMP: Unavailable by ICMP ping
Advanced ICMP: High packet loss
```

com disponibilidade baseada em:

```text
max(/Advanced ICMP Ping with Jitter/advanced.ping.rcv,#3)=0
```

e dependências explícitas de `Advanced ICMP: Collector error`, evitando que uma falha do coletor seja reportada como indisponibilidade de rede.

## Migração limpa recomendada

### 1. Faça backup antes de alterar vínculos

Exporte o template atualmente instalado e, em ambientes importantes, faça o backup normal do Zabbix/banco de dados utilizado pela sua organização antes de limpar entidades herdadas.

### 2. Inspecione o host antes de remover qualquer objeto

Acesse:

```text
Data collection > Hosts > <host> > Triggers
```

e pesquise por:

```text
advanced.ping
ICMP ping
```

Revise também os templates vinculados ao host.

Os triggers mantidos atualmente usam o prefixo:

```text
Advanced ICMP:
```

Triggers legados sem esse prefixo devem ser revisados antes da exclusão. Não remova triggers de outros templates apenas por terem nomes semelhantes sem confirmar sua origem.

### 3. Se o template legado ainda estiver vinculado

Se a intenção for remover definitivamente os objetos antigos do AdvancedPING, utilize **Unlink and clear** no template legado em vez de apenas **Unlink**.

Use essa opção somente depois de confirmar que as entidades antigas não são mais necessárias. Se a continuidade histórica for importante, faça primeiro a migração em um host de teste e siga o processo normal de backup e controle de mudanças antes de limpar objetos em produção.

### 4. Se o template legado já estiver desvinculado

Se os objetos antigos foram preservados por um **Unlink** anterior, eles podem ter se tornado entidades locais do host. Revise-os individualmente e remova somente os objetos confirmadamente legados.

Identificadores úteis incluem:

```text
advanced.ping.avg
advanced.ping.loss
advanced.ping.max
advanced.ping.min
advanced.ping.rcv
advanced.ping.xmt
advanced.ping.jitter
advanced.ping.stddev
advanced.ping.error
```

A presença de uma key `advanced.ping.*` sozinha não é motivo suficiente para apagar um objeto, porque o template mantido utiliza intencionalmente o mesmo namespace de keys. Confirme se o objeto é herdado do template atual ou se é uma cópia local legada.

### 5. Importe/vincule o template mantido

Importe o export correspondente à versão principal do Zabbix instalada e vincule o **Advanced ICMP Ping with Jitter** ao host.

Depois confirme que o host recebeu os triggers mantidos esperados:

```text
Advanced ICMP: Collector error
Advanced ICMP: High jitter
Advanced ICMP: High packet loss
Advanced ICMP: High response time
Advanced ICMP: High RTT standard deviation
Advanced ICMP: High time differences (Min/Max)
Advanced ICMP: Long unavailable by ICMP ping
Advanced ICMP: Unavailable by ICMP ping
```

## Validação após a atualização

Valide pelo menos os seguintes cenários em um host de teste antes de ampliar a implantação em produção:

1. **Coleta normal** — `xmt=20`, `rcv=20` ou a quantidade esperada de respostas e `error=""`;
2. **Erro de configuração do coletor** — apenas `Advanced ICMP: Collector error` deve entrar em problema; os triggers de sintomas de rede devem permanecer suprimidos pela dependência;
3. **Recuperação** — ao restaurar uma configuração válida, o erro do coletor deve se resolver automaticamente;
4. **Destino realmente indisponível** — o coletor deve permanecer saudável (`error=""`), os pacotes enviados devem refletir a quantidade configurada, os pacotes recebidos devem ser `0` e os triggers de disponibilidade devem abrir conforme suas janelas configuradas;
5. **Sem alertas legados duplicados** — eventos antigos como `Unavailable by ICMP ping` / `High ICMP ping loss` não devem coexistir com os triggers mantidos `Advanced ICMP:`, exceto quando outro template intencionalmente vinculado também os forneça.

## Estratégia de validação mais segura

Para atualizações importantes, a forma mais segura de validar é criar um host temporário vinculado **somente** ao novo template. Isso elimina interferência de outros templates e de objetos locais legados. Depois de validar coletor, items, triggers, dependências e recuperação, migre os hosts de produção de forma controlada.
