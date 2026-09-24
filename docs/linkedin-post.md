# Post para LinkedIn

---

🎟️ E se a sua IA pudesse investigar um incidente de produção sozinha?

Montei um projetinho de estudo pra explorar uma ideia que tá cada vez mais forte: **observabilidade + IA**.

É uma API simples de venda de ingressos (Python + FastAPI + PostgreSQL), totalmente instrumentada com OpenTelemetry — traces, métricas e logs — enviando tudo para uma stack completa de observabilidade:

🔭 OpenTelemetry Collector
📊 Prometheus (métricas + alertas)
🔍 Tempo (traces distribuídos)
📝 Loki (logs)
📈 Grafana (visualização)

O pulo do gato: conectei o **Grafana MCP** à IDE. Com isso, dá pra perguntar em linguagem natural:

💬 "A aplicação começou a retornar erros 5xx e a latência subiu. Correlacione métricas, logs e traces dos últimos 15 minutos e me diga a causa raiz."

E a IA percorre a telemetria, cruza os sinais e chega na conclusão — no meu cenário de falha proposital (um vazamento de conexões que esgota o pool do banco), ela identifica o endpoint afetado, acha o log do vazamento e aponta o pool esgotado. 🤯

Não substitui o engenheiro — mas encurta MUITO o caminho entre "algo quebrou" e "achei o porquê".

Projeto baseado no material da pós de Engenharia de IA Aplicada, que adaptei pra um novo cenário e reescrevi em Python pra fixar o conteúdo.

Código aberto pra quem quiser rodar (`docker compose up` e pronto):
👉 https://github.com/AndreSantos09/ticketflow-observability

#Observability #OpenTelemetry #IA #DevOps #SRE #Grafana #Python #FastAPI #MCP #EngenhariaDeSoftware
