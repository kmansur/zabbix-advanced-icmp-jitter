# Migração do AdvancedPING legado

[English](../en/legacy-advancedping-upgrade.md) | [Português (Brasil)](legacy-advancedping-upgrade.md)

Um **Unlink** simples pode deixar entidades herdadas do AdvancedPING no host como objetos locais. Se a intenção for remover também esses objetos herdados do template legado, use **Unlink and clear** somente depois de revisar o impacto e seguir o processo normal de backup e controle de mudanças.

Antes da aplicação ampla, valide em um host temporário limpo e procure triggers legadas duplicadas, como `Unavailable by ICMP ping` ou `High ICMP ping loss`. O template mantido usa o prefixo `Advanced ICMP:` nas triggers.

Não remova um objeto apenas porque ele utiliza uma chave `advanced.ping.*`; o template mantido usa o mesmo namespace. Confirme primeiro a origem do objeto.
