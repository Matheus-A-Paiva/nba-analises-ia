# NBA Analises IA — Backend

API desenvolvida em FastAPI para coleta, tratamento e disponibilização de dados da NBA, com suporte a análise gerada por IA para comparação entre equipes.

## Visão do projeto

Este backend é responsável por concentrar a lógica de dados do sistema. Ele consulta estatísticas oficiais da NBA, organiza as informações por time e jogador, monta o histórico de confrontos diretos e fornece uma análise textual baseada em IA.

## Objetivo

O objetivo do backend é oferecer uma base confiável de dados para o frontend, permitindo:

- visualizar jogos futuros
- comparar dois times com estatísticas detalhadas em chamadas separadas
- identificar jogadores em destaque
- consultar confrontos anteriores
- gerar análise automática com IA

## Tecnologias utilizadas

- Python
- FastAPI
- nba_api
- pandas
- SQLAlchemy
- JWT
- Google Gemini

## Estrutura funcional

### 1. Coleta de dados
Os dados são obtidos por meio dos endpoints oficiais da NBA. O projeto usa dados estáticos da biblioteca `nba_api` e faz chamadas HTTP diretas para os endpoints de estatísticas mais sensíveis a timeout.

### 2. Processamento
As informações coletadas são tratadas para calcular médias por jogo, selecionar destaques por categoria e organizar o histórico de confrontos.

### 3. Análise com IA
A API integra Google Gemini para gerar um resumo simples e interpretável sobre o confronto entre duas equipes.

## Principais endpoints

### `POST /auth/register`
Cria uma conta e retorna um bearer token para uso nos endpoints protegidos.

### `POST /auth/login`
Autentica um usuário existente e retorna um bearer token.

### `GET /games?date=YYYY-MM-DD`
Retorna os jogos da data informada. O frontend deve chamar esse endpoint uma vez por data necessária, por exemplo hoje, amanhã e depois de amanhã.

### `GET /teams/{team_id}`
Retorna o bloco reutilizável de um time, incluindo:

- dados básicos dos times
- estatísticas de temporada
- melhores jogadores por categoria

### `GET /matchups/{team1_id}/{team2_id}/history`
Retorna os confrontos diretos recentes entre duas equipes.

### `GET /matchups/{team1_id}/{team2_id}/top-scorers?limit=15`
Retorna os principais pontuadores considerando apenas as duas equipes selecionadas.

### `GET /matchups/{team1_id}/{team2_id}/top-players?limit=10`
Retorna os líderes por métrica entre as duas equipes selecionadas.

### `GET /analysis/{team1_id}/{team2_id}`
Retorna uma análise em linguagem natural com apoio de IA, destacando qual equipe está melhor no geral e quais são as principais vantagens de cada lado.

## Autenticação

Os endpoints de dados exigem JWT bearer token.

Fluxo esperado:

1. chamar `POST /auth/register` ou `POST /auth/login`
2. copiar o `access_token` retornado
3. enviar `Authorization: Bearer <token>` nas chamadas para jogos, times, matchups, jogadores e análise

## Dados retornados

### Time
Cada time contém:

- id
- nome
- sigla
- logo

### Estatísticas de temporada

- pontos por jogo
- pontos sofridos
- rebotes
- assistências
- turnovers
- aproveitamento de arremesso de quadra

### Jogadores em destaque
O backend identifica líderes da equipe em:

- pontos
- rebotes
- assistências
- roubos
- bloqueios
- turnovers
- FG%
- 3P%

### Pontuadores em destaque
Os endpoints de matchup retornam jogadores ordenados por pontos por jogo, com foto quando disponível.

## Fotos dos jogadores

As fotos são montadas automaticamente a partir do ID do jogador usando a CDN oficial da NBA.

Formato utilizado:

```bash
https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png
```

## Como executar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
copy .env.example .env
```

Defina pelo menos:

- `DATABASE_URL`
- `SECRET_KEY`
- `GEMINI_API_KEY`

### 3. Iniciar a API

```bash
uvicorn app.main:app --reload
```

## Exemplo de uso

Exemplos de consumo pelo frontend:

- `POST /auth/login` para obter o bearer token
- `GET /games?date=2026-04-15` para os jogos de uma data específica
- `GET /teams/1610612755` para o resumo reutilizável de um time
- `GET /matchups/1610612755/1610612753/history` para confrontos recentes
- `GET /matchups/1610612755/1610612753/top-scorers?limit=15` para os pontuadores do confronto
- `GET /matchups/1610612755/1610612753/top-players?limit=10` para líderes por métrica
- `GET /players/top-scorers?limit=15` para líderes de pontuação
- `GET /analysis/{team1_id}/{team2_id}` para o resumo em linguagem natural

## Deploy

O projeto já está preparado para deploy em uma plataforma como Render com:

- entrypoint em `app.main`
- banco PostgreSQL configurável por `DATABASE_URL`
- healthcheck público em `GET /health`
- arquivo `render.yaml` com `startCommand` e `healthCheckPath`
- normalização automática da connection string do Render para uso com `asyncpg`

Variáveis mínimas para produção:

- `DATABASE_URL`
- `SECRET_KEY`
- `GEMINI_API_KEY`
- `CORS_ORIGINS`

Antes de subir, ajuste `CORS_ORIGINS` para os domínios reais do frontend.

Fluxo recomendado para a tela de confronto no frontend:

1. buscar `GET /teams/{team1_id}`
2. buscar `GET /teams/{team2_id}`
3. buscar `GET /matchups/{team1_id}/{team2_id}/history`
4. buscar `GET /matchups/{team1_id}/{team2_id}/top-scorers?limit=15`
5. buscar `GET /matchups/{team1_id}/{team2_id}/top-players?limit=10`
6. opcionalmente buscar `GET /analysis/{team1_id}/{team2_id}`

## Observações

- O sistema foi pensado para ser modular e simples de evoluir.
- As estatísticas podem ser expandidas futuramente com novos indicadores.
- Em caso de indisponibilidade da IA, o restante da API continua operando normalmente.
- A documentação interativa mais completa fica em `/docs` quando a API está em execução.
- Os endpoints agregados antigos não fazem mais parte do contrato suportado; o frontend deve montar a tela de confronto com chamadas separadas.
