"""TicketFlow - a tiny ticket-selling API used to demo observability + AI.

Endpoints:
  GET  /health           -> liveness check
  GET  /events           -> list events with availability
  POST /events/{id}/buy  -> buy tickets for an event

The POST endpoint is where the (optional) failure scenario lives: when
SCENARIO_LEAKY_CONNECTIONS is enabled, every purchase leaks a DB connection,
so the pool exhausts and latency/errors spike - all visible in Grafana.
"""
import logging

from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from pydantic import BaseModel, Field

# Telemetry must be initialised before anything is instrumented.
from otel import setup_telemetry

setup_telemetry()

import db  # noqa: E402  (import after telemetry setup)
from config import config  # noqa: E402

logger = logging.getLogger("ticketflow")
tracer = trace.get_tracer("ticketflow")
meter = metrics.get_meter("ticketflow")

tickets_sold_counter = meter.create_counter(
    "ticketflow.tickets_sold",
    unit="{ticket}",
    description="Number of tickets sold",
)

# Keep references to leaked connections so the GC can't reclaim them.
# This is what makes the failure scenario a genuine leak.
_leaked_connections: list = []

app = FastAPI(title="TicketFlow API", version="1.0.0")


class BuyRequest(BaseModel):
    buyer: str = Field(..., min_length=1, examples=["ana@example.com"])
    quantity: int = Field(..., gt=0, le=10, examples=[2])


@app.on_event("startup")
def on_startup() -> None:
    db.open_pool()
    db.init_schema()
    PsycopgInstrumentor().instrument(enable_commenter=True)
    logger.info(
        "TicketFlow started (leaky_connections_scenario=%s)",
        config.SCENARIO_LEAKY_CONNECTIONS,
    )


@app.on_event("shutdown")
def on_shutdown() -> None:
    db.close_pool()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/events")
def list_events() -> dict:
    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, venue, total_seats, sold_seats "
                "FROM events ORDER BY id;"
            )
            rows = cur.fetchall()
    events = [
        {
            "id": r[0],
            "name": r[1],
            "venue": r[2],
            "total_seats": r[3],
            "sold_seats": r[4],
            "available": r[3] - r[4],
        }
        for r in rows
    ]
    return {"events": events}


@app.post("/events/{event_id}/buy")
def buy_tickets(event_id: int, body: BuyRequest) -> dict:
    with tracer.start_as_current_span("buy_tickets") as span:
        span.set_attribute("ticketflow.event_id", event_id)
        span.set_attribute("ticketflow.quantity", body.quantity)

        if config.SCENARIO_LEAKY_CONNECTIONS:
            # BUG (on purpose): grab a connection from the pool and never
            # return it. After max_size purchases the pool is exhausted and
            # every request starts timing out.
            leaked = db.pool.getconn()
            _leaked_connections.append(leaked)
            logger.warning(
                "Leaked a DB connection (total leaked=%d)",
                len(_leaked_connections),
            )

        with db.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT total_seats, sold_seats FROM events "
                    "WHERE id = %s FOR UPDATE;",
                    (event_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Event not found")

                total_seats, sold_seats = row
                available = total_seats - sold_seats
                if body.quantity > available:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Not enough seats (available={available})",
                    )

                cur.execute(
                    "UPDATE events SET sold_seats = sold_seats + %s WHERE id = %s;",
                    (body.quantity, event_id),
                )
                cur.execute(
                    "INSERT INTO tickets (event_id, buyer, quantity) "
                    "VALUES (%s, %s, %s) RETURNING id;",
                    (event_id, body.buyer, body.quantity),
                )
                (ticket_id,) = cur.fetchone()
                conn.commit()

        tickets_sold_counter.add(body.quantity, {"event_id": str(event_id)})
        logger.info(
            "Sold %d ticket(s) for event %d to %s",
            body.quantity,
            event_id,
            body.buyer,
        )
        return {
            "ticket_id": ticket_id,
            "event_id": event_id,
            "buyer": body.buyer,
            "quantity": body.quantity,
        }


# Instrument FastAPI (HTTP server spans + metrics).
FastAPIInstrumentor.instrument_app(app)
