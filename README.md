# NBA Analises IA — Backend

API desenvolvida em FastAPI para coleta, tratamento e disponibilização de dados da NBA, com suporte a análise gerada por IA para comparação entre equipes.

## Visão do projeto

Este backend é responsável por concentrar a lógica de dados do sistema. Ele consulta estatísticas oficiais da NBA, organiza as informações por time e jogador, monta o histórico de confrontos diretos e fornece uma análise textual baseada em IA.

## Objetivo

O objetivo do backend é oferecer uma base confiável de dados para o frontend, permitindo:

- visualizar jogos futuros
- comparar dois times com estatísticas detalhadas
- identificar jogadores em destaque
- consultar confrontos anteriores
- gerar análise automática com IA

## Tecnologias utilizadas

- Python
- FastAPI
- nba_api
- pandas
- requests
- Ollama

## Estrutura funcional

### 1. Coleta de dados
Os dados são obtidos por meio da biblioteca `nba_api`, que permite consultar times, jogadores, jogos e estatísticas atualizadas.

### 2. Processamento
As informações coletadas são tratadas para calcular médias por jogo, selecionar destaques por categoria e organizar o histórico de confrontos.

### 3. Análise com IA
A API integra Ollama para gerar um resumo simples e interpretável sobre o confronto entre duas equipes.

## Principais endpoints

### `GET /games/upcoming`
Retorna os próximos jogos disponíveis, com data, horário e informações dos times.

### `GET /match/{team1_id}/{team2_id}`
Retorna a comparação completa entre duas equipes, incluindo:

- dados básicos dos times
- estatísticas de temporada
- melhores jogadores por categoria
- histórico de confrontos diretos
- lista de pontuadores em destaque

### `GET /analysis/{team1_id}/{team2_id}`
Retorna uma análise em linguagem natural com apoio de IA, destacando qual equipe está melhor no geral e quais são as principais vantagens de cada lado.

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
O endpoint de confronto também retorna até 15 jogadores ordenados por pontos por jogo, com foto quando disponível.

## Fotos dos jogadores

As fotos são montadas automaticamente a partir do ID do jogador usando a CDN oficial da NBA.

Formato utilizado:

```bash
https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png
```

## Como executar

### 1. Instalar dependências

```bash
pip install fastapi uvicorn nba_api pandas requests
```

### 2. Instalar e iniciar o Ollama

```bash
irm https://ollama.com/install.ps1 | iex
ollama run llama3:8b
```

### 3. Iniciar a API

```bash
uvicorn main:app --reload
```

## Exemplo de uso

O backend pode ser consumido pelo frontend por meio das rotas de jogos futuros, confronto e análise com IA.

## Observações

- O sistema foi pensado para ser modular e simples de evoluir.
- As estatísticas podem ser expandidas futuramente com novos indicadores.
- Em caso de indisponibilidade da IA, o restante da API continua operando normalmente.
