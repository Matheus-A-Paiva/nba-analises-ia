# Sugestão de Branch

`feature/backend-auth-cache-matchups-deploy`

# Título do PR

`refactor: consolidar backend em app.main, dividir matchups, estabilizar integrações NBA e preparar deploy`

# Corpo do PR

## Contexto

Este PR consolida o backend em uma única aplicação FastAPI canônica, remove o fluxo legado baseado em `main.py`, estabiliza os endpoints mais sensíveis a timeout da NBA, divide o antigo endpoint agregado de confronto em chamadas menores para o frontend e prepara o projeto para deploy.

## Principais mudanças

### 1. Consolidação da aplicação

- remoção do `main.py` legado
- adoção definitiva de `app.main` como entrypoint da API
- organização da aplicação por routers, services, schemas, auth e database

### 2. Autenticação e estrutura base

- adição de autenticação JWT com `register` e `login`
- criação do modelo `User` com persistência via SQLAlchemy async
- centralização de settings com `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `CORS_ORIGINS` e demais parâmetros de ambiente

### 3. Endpoints de jogos e dados da NBA

- substituição do fluxo agregado de jogos por `GET /games?date=YYYY-MM-DD`
- aplicação de cache com `X-Cache` e `Cache-Control`
- documentação OpenAPI mais clara para consumo pelo frontend

### 4. Refactor do fluxo de confronto

- remoção do endpoint agregado `GET /match/{team1_id}/{team2_id}`
- criação de endpoints menores e mais previsíveis:
  - `GET /teams/{team_id}`
  - `GET /matchups/{team1_id}/{team2_id}/history`
  - `GET /matchups/{team1_id}/{team2_id}/top-scorers`
  - `GET /matchups/{team1_id}/{team2_id}/top-players`
- alinhamento do contrato para o frontend montar a tela de confronto com chamadas separadas

### 5. Estabilização das integrações com stats.nba.com

- substituição dos hot paths mais frágeis do `nba_api` por chamadas HTTP diretas com `curl_cffi` e impersonation de navegador
- uso de parâmetros estáveis para `scoreboardv2`, `leaguedashteamstats`, `leaguedashplayerstats` e `leaguegamefinder`
- remoção da dependência do `LeagueGameFinder` no histórico de confronto
- manutenção de cache em memória com fallback para stale quando aplicável

### 6. Análise por IA

- manutenção do endpoint `GET /analysis/{team1_id}/{team2_id}` como responsabilidade do backend
- migração do provedor legado para Gemini
- tratamento de respostas truncadas do Gemini com retry e fallback determinístico baseado nas estatísticas carregadas

### 7. OpenAPI, documentação e DX

- melhoria do `/docs` com summaries, descriptions, operation ids, schemas e respostas documentadas
- explicitação do esquema `BearerAuth` no OpenAPI
- documentação de headers de cache nos endpoints relevantes
- atualização do `README.md` com o novo contrato da API, novo fluxo do frontend e seção de deploy

### 8. Preparação para deploy

- adição de `Dockerfile`
- adição de `.dockerignore`, `.gitignore` e `.env.example`
- criação de `render.yaml` com `buildCommand`, `startCommand`, banco vinculado e `healthCheckPath`
- adição de endpoint público `GET /health`

## Endpoints suportados após este PR

### Públicos

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`

### Protegidos por Bearer token

- `GET /games?date=YYYY-MM-DD`
- `GET /teams/{team_id}`
- `GET /matchups/{team1_id}/{team2_id}/history`
- `GET /matchups/{team1_id}/{team2_id}/top-scorers?limit=15`
- `GET /matchups/{team1_id}/{team2_id}/top-players?limit=10`
- `GET /players/top-scorers?limit=15`
- `GET /analysis/{team1_id}/{team2_id}`

## Remoções importantes

- remoção de `main.py`
- remoção do endpoint agregado `GET /match/{team1_id}/{team2_id}`
- remoção do contrato antigo baseado em fluxo monolítico de confronto

## Validações executadas

- teste de registro e autenticação JWT
- teste do endpoint `GET /games?date=...` com cache `miss` e `hit`
- teste de `GET /players/top-scorers`
- teste dos novos endpoints de `matchups`
- confirmação de remoção do endpoint antigo `/match/...`
- validação de `/openapi.json` com `BearerAuth`
- validação de `/health` retornando `200`
- validação da correção da resposta truncada do endpoint de análise

## Impacto para o frontend

O frontend deve parar de chamar `/match/{team1_id}/{team2_id}` e montar a tela de confronto com chamadas separadas. O fluxo recomendado é:

1. buscar `GET /teams/{team1_id}`
2. buscar `GET /teams/{team2_id}`
3. buscar `GET /matchups/{team1_id}/{team2_id}/history`
4. buscar `GET /matchups/{team1_id}/{team2_id}/top-scorers?limit=15`
5. buscar `GET /matchups/{team1_id}/{team2_id}/top-players?limit=10`
6. opcionalmente buscar `GET /analysis/{team1_id}/{team2_id}`

## Observações

- o `docker-compose.yml` atual sobe apenas o PostgreSQL local
- a criação de tabelas continua sendo feita com `create_all` no startup
- migrations com Alembic podem ser adicionadas depois, mas não são bloqueantes para o primeiro deploy

# Checklist de Deploy no Render

## Web Service

- Runtime: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

## Banco

- Criar o database `nba-db`
- Garantir que a variável `DATABASE_URL` venha do `connectionURI` do banco

## Variáveis obrigatórias

- `DATABASE_URL`: vincular ao banco do Render
- `SECRET_KEY`: gerar valor forte em produção
- `GEMINI_API_KEY`: chave real do Gemini
- `CORS_ORIGINS`: domínios reais do frontend, separados por vírgula

## Exemplo de `CORS_ORIGINS`

```env
https://seu-frontend.onrender.com,https://seu-dominio.com
```

## Smoke test pós-deploy

1. abrir `/health`
2. abrir `/docs`
3. testar `POST /auth/register`
4. testar `GET /games?date=2026-04-15` com bearer token
5. testar `GET /analysis/{team1_id}/{team2_id}`
