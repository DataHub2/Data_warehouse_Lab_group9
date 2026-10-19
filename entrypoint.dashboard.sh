#!/usr/bin/env bash
# Entrypoint for the dashboard container.

## st.connection("snowflake") reads .streamlit/secrets.toml.
## Both the key file and the secrets file are written here from environment variables, 
## therefore, the container will get the credentials without them ever being committed.
set -euo pipefail

mkdir -p /app/.keys /app/dashboard/.streamlit

## LLM fix: -> Rebuild the PEM from the single-line base64 in the environment.
## Fold restores the 64-character lines needed for a PEM file.
{
  echo "-----BEGIN PRIVATE KEY-----"
  echo "$STREAMLIT_PRIVATE_KEY" | fold -w 64
  echo "-----END PRIVATE KEY-----"
} > /app/.keys/streamlit_key.p8
chmod 600 /app/.keys/streamlit_key.p8

cat > /app/dashboard/.streamlit/secrets.toml <<EOF
[connections.snowflake]
account = "${SNOWFLAKE_ACCOUNT}"
user = "${STREAMLIT_USER}"
role = "${STREAMLIT_ROLE}"
warehouse = "flights_wh"
database = "flights_db"
schema = "marts"
private_key_file = "/app/.keys/streamlit_key.p8"
EOF
chmod 600 /app/dashboard/.streamlit/secrets.toml

cd /app/dashboard
exec uv run streamlit run app.py --server.port=8501 --server.address=0.0.0.0