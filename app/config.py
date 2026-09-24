"""Application configuration loaded from environment variables."""
import os


class Config:
    # HTTP server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "9000"))

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://ticketflow:ticketflow_dev_password@localhost:5433/ticketflow_app",
    )

    # OpenTelemetry
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "ticketflow")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
    )

    # Failure scenario toggle.
    # When enabled, each purchase intentionally leaks a DB connection so the
    # connection pool exhausts over time - a realistic bug to diagnose with AI.
    SCENARIO_LEAKY_CONNECTIONS: bool = (
        os.getenv("SCENARIO_LEAKY_CONNECTIONS", "false").lower() == "true"
    )


config = Config()
