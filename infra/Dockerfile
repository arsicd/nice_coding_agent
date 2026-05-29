FROM paradedb/paradedb:latest

LABEL org.opencontainers.image.description="PostgreSQL with ParadeDB (pg_search) + pgvector, preconfigured. Based on paradedb/paradedb, licensed AGPL-3.0. Source: https://github.com/paradedb/paradedb"
LABEL org.opencontainers.image.licenses="AGPL-3.0"

COPY ./init.sql /docker-entrypoint-initdb.d/

ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=mysecretpassword
ENV POSTGRES_DB=nice_agent_db