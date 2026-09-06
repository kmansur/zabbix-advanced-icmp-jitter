# Política de Segurança

[English](SECURITY.md) | **Português (Brasil)**

## Versões suportadas

Correções de segurança são fornecidas para a versão mais recente mantida do projeto.

Status atual de compatibilidade:

| Componente | Status |
| --- | --- |
| Template Zabbix 7.0 | Suportado |
| Template Zabbix 8.0 | Testado no Zabbix 8.0 Beta 2; será revalidado conforme novas Beta/RC/versão final forem testadas |
| Coletor Python | Suportado com a versão atual do template |

Versões históricas podem receber correções somente quando for viável.

## Relatando uma vulnerabilidade

**Não** abra uma issue pública no GitHub para relatar uma vulnerabilidade de segurança.

Use o fluxo privado de GitHub Security Advisory do repositório:

`Security` > `Advisories` > `Report a vulnerability`

Inclua, quando possível:

- versão afetada do projeto;
- versão e build exata do Zabbix;
- sistema operacional do Zabbix Server/Proxy;
- versões do Python e `fping`;
- passos mínimos para reprodução;
- comportamento esperado e observado;
- impacto potencial;
- logs ou saída do coletor devidamente sanitizados.

Nunca inclua senhas, tokens de API, chaves privadas, credenciais de produção ou outros segredos no relato.

## Escopo de segurança

Áreas sensíveis à segurança incluem:

- tratamento de valores de host e macros passados ao coletor externo;
- construção e execução do subprocesso `fping`;
- parsing da saída de comandos externos;
- workflows de release e CI;
- alterações de template que possam executar comandos inesperados ou expor dados sensíveis.

O coletor invoca `fping` usando uma lista de argumentos em vez de uma string de comando via shell. Alterações nesse comportamento exigem revisão adicional de segurança e testes.
