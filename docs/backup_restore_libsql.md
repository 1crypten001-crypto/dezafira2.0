# 💾 Backup e Restore do banco da DezafiraClube (libsql-server)

O banco da vitrine/vendas/membros fica no serviço **libsql-server** do Railway.
Este guia cobre os 2 níveis de proteção e como se recuperar de cada cenário.

## Níveis de proteção

| Nível | O que é | Frequência | RPO (perda máx.) |
|---|---|---|---|
| **1. Bottomless (S3)** | Replicação contínua do WAL para um Railway Bucket | Contínuo (tempo real) | ~1s |
| **2. Snapshot do volume** | Tarball do `/var/lib/sqld` (banco inteiro) | Manual / sob demanda | desde o último snapshot |

> Ambos exigem o **volume persistente** em `/var/lib/sqld` + as variáveis do `libsql-server/.env.example`.

---

## 🧪 Teste de restore (recomendado: faça 1x antes de precisar)

> Testar o restore **num ambiente descartável** evita surpresas em produção.

### Teste via snapshot do volume (mais simples)

```bash
# 1) Baixa o volume inteiro (banco + WAL) do serviço para a sua máquina
railway volume files download / ./libsql-backup.tar --service libsql-server

# 2) Verifica o conteúdo
tar -tf libsql-backup.tar | head -20   # deve conter iku.db (e iku.db-wal)

# 3) Restaura num diretório local e valida o banco
mkdir -p /tmp/restore-test && tar -xf libsql-backup.tar -C /tmp/restore-test
# abre com qualquer cliente sqlite e confere os settings do branding:
#   SELECT * FROM settings WHERE key IN ('site_title','site_description');
```

### Teste via bottomless (a proteção de verdade)

```bash
# 1) Sobe um container temporário com a MESMA imagem e as MESMAS variáveis
#    do libsql-server, MAS sem o volume (dados descartáveis):
#    Railway → New Service → Docker Image: ghcr.io/tursodatabase/libsql-server:v0.24.32
#    (copie as variáveis LIBSQL_BOTTOMLESS_* do serviço de produção)
#
# 2) Roda o restore no container temporário:
railway ssh --service <servico-temporario>
bash <(curl -fsSL https://raw.githubusercontent.com/1crypten001-crypto/dezafira2.0/main/libsql-server/restore.sh)

# 3) Confere que o banco veio íntegro (o script já roda integrity_check):
ls -la /var/lib/sqld/iku.db
#     → deve existir e ter dados (ex.: SELECT de settings com 'DezafiraClube')
```

---

## 🔄 Restore de verdade (produção)

Cenário: o volume zerou ou corrompeu (deploy com volume desmontado, erro manual).

> Não dá para `railway ssh` num serviço parado — o restore é feito num **container temporário**
> (mesma imagem e variáveis, sem volume) e o banco restaurado é enviado de volta ao volume.

```bash
# 1) Container temporário com a MESMA imagem e as MESMAS variáveis LIBSQL_BOTTOMLESS_*
#    (Railway → New Service → Docker Image: ghcr.io/tursodatabase/libsql-server:v0.24.32)

# 2) Restaura a geração mais recente dentro dele:
railway volume files upload ./restore.sh /restore.sh --service <servico-temp>
railway ssh --service <servico-temp>
bash /restore.sh        # baixa do bucket, verifica integridade, gera /var/lib/sqld/iku.db

# 3) Envia o banco restaurado para o volume de produção:
railway volume files upload /var/lib/sqld/iku.db /var/lib/sqld/iku.db --service libsql-server
#    (deixe o serviço de produção PARADO enquanto isso — Settings → 0 réplicas)

# 4) Sobe o serviço de volta. O sqld abre o banco restaurado e retoma a replicação:
railway redeploy --service libsql-server
```

> O script de restore **não roda com o sqld vivo** (proteção contra escrita concorrente).
> Se o volume estiver intacto e você só quiser uma geração anterior, dá para usar o
> snapshot do volume (seção de teste) ou `bottomless-cli restore -g <geração>`.

---

## 🧹 Manutenção do bucket

```bash
# Lista as gerações salvas (snapshots do WAL)
railway ssh --service libsql-server -- bottomless-cli ls -v

# Snapshot manual imediato (força upload do estado atual)
railway ssh --service libsql-server -- bottomless-cli snapshot

# Remover gerações antigas (ex.: mais velhas que 30 dias)
railway ssh --service libsql-server -- bottomless-cli rm --older-than 2026-07-01
```

> ⚠️ A replicação bottomless precisa das variáveis `LIBSQL_BOTTOMLESS_*` do
> `.env.example` ativas. Confira o funcionamento:
> `railway logs --service libsql-server | grep -i bottomless` → deve mostrar
> `replicator started` e uploads periódicos.

---

## 🧯 Pior caso: restaurar do zero (conta nova / projeto novo)

1. Suba um libsql-server novo (mesmas variáveis, inclusive `LIBSQL_BOTTOMLESS_*`)
2. Rode o `restore.sh` (o namespace `LIBSQL_BOTTOMLESS_DATABASE_ID` deve ser o mesmo)
3. Aponte a DezafiraClube para o novo serviço (`DATABASE_URL`) e teste o `/healthz`
