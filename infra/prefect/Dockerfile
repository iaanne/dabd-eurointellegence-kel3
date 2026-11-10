FROM docker.io/prefecthq/prefect:3-python3.12

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY flows ./flows
COPY prefect.yaml ./
COPY infra/prefect/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN pip install --no-cache-dir -e ".[prefect,iceberg]" \
    && chmod 755 /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
