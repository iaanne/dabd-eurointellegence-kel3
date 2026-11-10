START ?= $(shell date -d '7 days ago' +%F)
END ?= $(shell date -d 'yesterday' +%F)

.PHONY: setup test demo demo-power demo-price demo-weather demo-entsoe list show docs clean prefect-up prefect-down prefect-deploy prefect-run prefect-logs publish-iceberg sync-bronze

setup:
	uv sync --extra dev

test:
	uv run pytest

docs:
	uv run --with markdown --with weasyprint python scripts/build_docs.py

demo-power:
	uv run eurogrid ingest-energy-charts --dataset public_power --country de --start $(START) --end $(END)

demo-price:
	uv run eurogrid ingest-energy-charts --dataset price --bzn DE-LU --start $(START) --end $(END)

demo-weather:
	uv run eurogrid ingest-weather --location berlin --latitude 52.52 --longitude 13.41 --start $(START) --end $(END)

demo-entsoe:
	uv run eurogrid ingest-entsoe --start $(START) --end $(END)

demo: demo-power demo-price demo-weather demo-entsoe

list:
	uv run eurogrid list

show:
	uv run eurogrid show --dataset $(or $(DATASET),public_power)

publish-iceberg:
	uv run --extra iceberg eurogrid publish-iceberg

sync-bronze:
	uv run eurogrid sync-bronze

clean:
	rm -rf data .pytest_cache

prefect-up:
	podman-compose -p eurogrid up -d prefect-server prefect-worker

prefect-down:
	podman-compose -p eurogrid stop prefect-server prefect-worker

prefect-deploy:
	podman exec eurogrid-prefect-worker prefect deploy --all --prefect-file /app/prefect.yaml

prefect-run:
	podman exec eurogrid-prefect-worker prefect deployment run 'bronze-daily/production'

prefect-logs:
	podman logs -f eurogrid-prefect-worker