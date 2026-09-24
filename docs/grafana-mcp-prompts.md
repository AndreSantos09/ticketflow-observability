# Grafana MCP — Prompts de Exemplo

Depois de subir a stack, você pode conectar o **Grafana MCP** (rodando em
`http://localhost:8000/mcp`) à sua IDE com IA (Cursor, Windsurf, Kiro, etc.) e
consultar métricas, logs, traces e alertas **em linguagem natural**.

## Contexto da aplicação

- **App**: API FastAPI (Python) de venda de ingressos, instrumentada com OpenTelemetry
- **Datasources**: Prometheus (métricas), Loki (logs), Tempo (traces)
- **Serviços de apoio**: PostgreSQL, OpenTelemetry Collector, Blackbox Exporter

---

## 📊 Métricas HTTP

```
Consulte no Prometheus a taxa de requisições e a latência p95 da aplicação
ticketflow na última hora. Use a métrica http_server_duration_milliseconds
(labels http_target e http_status_code). Mostre a taxa e o p95 por rota.
```

## 🎟️ Vendas de ingressos

```
Quantos ingressos foram vendidos por evento nos últimos 15 minutos?
Use a métrica ticketflow_tickets_sold_total.
```

## 🔥 Alertas disparando

```
Liste todos os alertas que estão em estado "firing" no Prometheus, com
severidade, descrição e há quanto tempo estão ativos.
```

## 🐌 Diagnóstico do cenário de falha (leaky connections)

Rode a app com `SCENARIO_LEAKY_CONNECTIONS=true`, gere carga com
`./scripts/generate-load.sh` e peça para a IA investigar:

```
A aplicação ticketflow começou a retornar erros 5xx e a latência subiu.
Correlacione métricas, logs e traces das últimas 15 minutos e me diga qual
é a causa raiz provável do problema.
```

Esperado: a IA identifica o aumento de erros/latência no endpoint
`POST /events/{event_id}/buy`, encontra nos logs a mensagem
`Leaked a DB connection` e conclui que o pool de conexões do banco está
sendo esgotado.

## 🔍 Logs com trace ID

```
Busque no Loki mensagens de log com nível warning/erro da aplicação
ticketflow nos últimos 30 minutos e mostre os trace IDs associados.
```

## 🧭 Mapa de dependências (traces)

```
Use o Tempo para gerar o mapa de dependências de serviços e mostre o fluxo
de uma requisição de compra de ingresso (buy_tickets), incluindo as
operações no PostgreSQL.
```

---

## Dicas para prompts eficazes

1. **Janela de tempo**: sempre informe o intervalo ("última hora", "últimos 30 min").
2. **Filtros por label**: filtre por `service.name`, rota (`http_route`) ou `job`.
3. **Agregações**: peça `rate()`, `avg()`, `p95` para respostas mais úteis.
4. **Correlação**: use trace IDs para saltar entre logs (Loki) e traces (Tempo).
5. **Alertas**: peça severidade, duração e serviço afetado.
