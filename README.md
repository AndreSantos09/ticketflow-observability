# 🎟️ TicketFlow — Observabilidade com IA

Exemplo simples e didático de **observabilidade moderna integrada a IA**.

Uma pequena API de **venda de ingressos** (Python + FastAPI + PostgreSQL) é
totalmente instrumentada com **OpenTelemetry** (traces, métricas e logs) e
enviada para uma stack de observabilidade completa. Por cima, o **Grafana MCP**
permite que uma IA (na sua IDE) consulte métricas, logs, traces e alertas em
linguagem natural — e até diagnostique um problema de produção simulado.

> Projeto de estudo baseado no exemplo de observabilidade da pós de Engenharia
> de IA Aplicada, adaptado para o cenário de venda de ingressos e reescrito em
> Python/FastAPI.

## 🏗️ Arquitetura

```
┌──────────────┐
│ TicketFlow   │  (FastAPI)
│   API        │ ──────┐
└──────────────┘       │ OTLP (gRPC)
                       ▼
             ┌──────────────────────┐
             │ OpenTelemetry         │
             │ Collector             │
             └──────────────────────┘
             │           │          │
             ▼           ▼          ▼
        ┌────────┐  ┌────────┐  ┌──────────┐
        │ Tempo  │  │  Loki  │  │Prometheus│
        │(traces)│  │ (logs) │  │(métricas)│
        └────────┘  └────────┘  └──────────┘
             │           │          │
             └───────────┴──────────┘
                         ▼
                    ┌──────────┐        ┌─────────────┐
                    │ Grafana  │ ◀───── │ Grafana MCP │ ◀── IA / IDE
                    └──────────┘        └─────────────┘
```

A aplicação só envia telemetria para o **OpenTelemetry Collector** via OTLP. O
collector distribui para Tempo (traces), Loki (logs) e Prometheus (métricas), e
o **Grafana** unifica a visualização. O **Blackbox Exporter** faz health checks
externos dos serviços.

## 📦 Componentes

| Serviço | Papel | URL |
|---|---|---|
| TicketFlow API | Aplicação demo (FastAPI) | http://localhost:9000 |
| Grafana | Dashboards e exploração | http://localhost:3000 |
| Prometheus | Métricas e alertas | http://localhost:9090 |
| Tempo | Traces distribuídos | http://localhost:3200 |
| Loki | Agregação de logs | http://localhost:3100 |
| OTel Collector (métricas) | Métricas do próprio collector | http://localhost:8889/metrics |
| Blackbox Exporter | Health checks | http://localhost:9115 |
| Grafana MCP | Servidor MCP para IA | http://localhost:8000/mcp |
| PostgreSQL | Banco de dados | localhost:5433 |

## 🚀 Como rodar

Pré-requisitos: **Docker** e **Docker Compose**.

```bash
# Sobe toda a stack (infra + aplicação)
docker compose up --build

# Verifica o status
docker compose ps
```

Acesse o **Grafana** em http://localhost:3000 (login anônimo como Admin já
habilitado). O dashboard **TicketFlow — Application Metrics** já vem provisionado.

### Testando a API

```bash
# Lista eventos disponíveis
curl http://localhost:9000/events

# Compra 2 ingressos para o evento 1
curl -X POST http://localhost:9000/events/1/buy \
  -H 'Content-Type: application/json' \
  -d '{"buyer":"ana@example.com","quantity":2}'
```

### Gerando carga (para ter telemetria)

```bash
./scripts/generate-load.sh
```

## 🤖 Observabilidade com IA (Grafana MCP)

Com a stack no ar, o servidor **Grafana MCP** roda em `http://localhost:8000/mcp`.
Conecte-o à sua IDE com IA. Exemplo de config (Cursor/Windsurf):

```json
{
  "mcpServers": {
    "grafana": {
      "type": "sse",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Depois é só perguntar em linguagem natural. Veja
[`docs/grafana-mcp-prompts.md`](docs/grafana-mcp-prompts.md) para exemplos.

## 🐛 Cenário de falha: vazamento de conexões

O projeto inclui **um** cenário de falha realista e simples para exercitar o
diagnóstico com IA. Quando a variável `SCENARIO_LEAKY_CONNECTIONS=true`, cada
compra de ingresso **vaza uma conexão** do pool do banco. Como o pool é pequeno
(`max_size=5`), ele se esgota rapidamente e as requisições passam a falhar
(erros 5xx e latência alta).

```bash
# Sobe a stack com o cenário de falha ativado
SCENARIO_LEAKY_CONNECTIONS=true docker compose up --build

# Em outro terminal, gera carga
./scripts/generate-load.sh
```

Agora peça para a IA investigar (via Grafana MCP):

> A aplicação ticketflow começou a retornar erros 5xx e a latência subiu.
> Correlacione métricas, logs e traces dos últimos 15 minutos e diga qual é a
> causa raiz.

A IA deve correlacionar o pico de erros/latência no endpoint de compra com os
logs `Leaked a DB connection` e concluir que o pool de conexões está esgotado.

## 📁 Estrutura

```
ticketflow-observability/
├── docker-compose.yaml         # Stack completa (infra + app)
├── app/                        # Aplicação FastAPI
│   ├── main.py                 # Endpoints + métricas + cenário de falha
│   ├── otel.py                 # Setup do OpenTelemetry
│   ├── db.py                   # Pool de conexões + schema/seed
│   ├── config.py               # Configuração via env
│   └── Dockerfile
├── infra/                      # Stack de observabilidade
│   ├── docker-compose-infra.yaml
│   ├── otel-collector/
│   ├── prometheus/
│   ├── tempo/
│   ├── loki/
│   ├── blackbox/
│   └── grafana/
├── scripts/
│   └── generate-load.sh        # Gerador de carga
└── docs/
    └── grafana-mcp-prompts.md  # Prompts de exemplo para a IA
```

## 🛑 Parando

```bash
docker compose down          # Para os serviços
docker compose down -v       # Para e remove volumes
```

## 📚 Créditos

Baseado no material do módulo de fundamentos da pós de **Engenharia de IA
Aplicada**, adaptado para fins de estudo (novo domínio e stack em Python/FastAPI).
