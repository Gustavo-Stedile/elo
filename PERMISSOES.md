# Comunicação em canais e permissões

## Modelo

| Conceito | Descrição |
|---|---|
| **Cargo** | Papel dentro de um grêmio: nome, cor, `prioridade` e um conjunto de permissões. Todo grêmio nasce com o cargo padrão **Membro** (vale para todos) e **Administrador**. |
| **Permissão** | Bitmask. Escopo de canal: `VER_CANAL`, `LER_HISTORICO`, `ENVIAR_MENSAGENS`, `GERENCIAR_MENSAGENS`. Escopo de grêmio: `GERENCIAR_CANAIS`, `GERENCIAR_CARGOS`, `GERENCIAR_MEMBROS`, `GERENCIAR_GREMIO`, `ADMINISTRADOR`. |
| **Permissão por usuário no grêmio** | `permitir` / `negar` individuais no vínculo membro-grêmio. |
| **Sobrescrita de canal** | `permitir` / `negar` em um canal, para um **cargo** ou para um **usuário** (só permissões de escopo de canal). |

## Como a permissão efetiva é calculada

`domain/core/autorizacao.py` (funções puras, testadas em `tests/test_autorizacao.py`).

**No grêmio:** fundador = tudo. Senão, soma das permissões do cargo padrão + cargos do membro; se tiver `ADMINISTRADOR`, tudo; senão aplica as sobrescritas individuais do usuário (remove as negadas, soma as permitidas).

**No canal:** parte das permissões do grêmio e aplica, nesta ordem: sobrescrita do cargo padrão → sobrescritas dos cargos do membro (se algum permite, vale) → sobrescrita do próprio usuário (a mais específica). `ADMINISTRADOR` ignora tudo. Sem `VER_CANAL`, nenhuma outra permissão de canal vale.

Exemplos: canal privado = negar `VER_CANAL` ao cargo padrão e permitir a um cargo/usuário; canal de avisos = negar `ENVIAR_MENSAGENS` ao cargo padrão; silenciar alguém = negar `ENVIAR_MENSAGENS` àquele usuário no canal.

## Regras de segurança

* **Hierarquia:** só se gerencia cargos/membros de prioridade **estritamente menor** que a sua maior prioridade (fundador está acima de todos). O cargo padrão é exceção, pois vale para todos.
* **Sem escalada:** ninguém concede permissão que não possui (no grêmio, ou no canal, conforme o caso).
* O fundador não pode ser removido nem ter permissões alteradas. O cargo padrão não pode ser excluído nem receber `ADMINISTRADOR`.
* Quem não enxerga um canal recebe **404** (não revela canais privados). Quem enxerga mas não pode agir recebe **403**.
* Quem tem `GERENCIAR_CANAIS` sempre encontra o canal para poder corrigir permissões, mas ler/enviar mensagens continua dependendo das permissões do canal.
* Mensagem só pode ser editada pelo autor; apagada pelo autor ou por quem tem `GERENCIAR_MENSAGENS`.

## Endpoints (todos exigem `Authorization: Bearer <token>`)

| Método | Rota | Exige |
|---|---|---|
| GET | `/gremio/` | meus grêmios |
| GET | `/gremio/{id}` · `/gremio/{id}/permissoes/me` | ser membro |
| GET/POST | `/gremio/{id}/membros/` | membro / `GERENCIAR_MEMBROS` |
| DELETE | `/gremio/{id}/membros/{usuario}` | `GERENCIAR_MEMBROS` (ou o próprio id = sair) |
| PUT/DELETE | `/gremio/{id}/membros/{usuario}/cargos/{cargo}` | `GERENCIAR_CARGOS` |
| PUT | `/gremio/{id}/membros/{usuario}/permissoes` | `GERENCIAR_CARGOS` |
| GET/POST | `/gremio/{id}/cargos/` | membro / `GERENCIAR_CARGOS` |
| PATCH/DELETE | `/gremio/{id}/cargos/{cargo}` | `GERENCIAR_CARGOS` |
| GET/POST | `/gremio/{id}/canais/` | só canais visíveis / `GERENCIAR_CANAIS` |
| GET | `/canal/{id}` (inclui `minhas_permissoes`) | `VER_CANAL` |
| PATCH/DELETE | `/canal/{id}` | `GERENCIAR_CANAIS` |
| GET | `/canal/{id}/permissoes` | `GERENCIAR_CANAIS` |
| PUT/DELETE | `/canal/{id}/permissoes/cargos/{cargo}` | `GERENCIAR_CANAIS` |
| PUT/DELETE | `/canal/{id}/permissoes/usuarios/{usuario}` | `GERENCIAR_CANAIS` |
| GET | `/canal/{id}/mensagens/?limite=&antes_de=&depois_de=` | `VER_CANAL` + `LER_HISTORICO` |
| POST | `/canal/{id}/mensagens/` | `VER_CANAL` + `ENVIAR_MENSAGENS` |
| PATCH | `/canal/{id}/mensagens/{msg}` | autor + `ENVIAR_MENSAGENS` |
| DELETE | `/canal/{id}/mensagens/{msg}` | autor, ou `GERENCIAR_MENSAGENS` |

`PUT` de permissões recebe `{"permitir": [...], "negar": [...]}` e **substitui** a sobrescrita atual; `[]` e `[]` a removem.
`GET .../mensagens/` devolve em ordem cronológica; use `depois_de=<último id>` para buscar só as novas (polling) e `antes_de=<primeiro id>` para paginar o histórico.

## Testes

```
python -m unittest discover -s tests -t . -v
```

* `test_autorizacao.py`: motor de permissões (puro).
* `test_servicos.py`: regras de negócio com repositórios em memória (`support.py`).
* `test_api_e2e.py`: fluxo HTTP completo; precisa de `fastapi`, `httpx`, `sqlalchemy`, `bcrypt`.

## Banco

`main.py` **não apaga mais o banco** ao iniciar. Para recriar do zero em desenvolvimento: `ELO_RESET_DB=1`. A URL pode ser trocada com `ELO_DATABASE_URL`.
