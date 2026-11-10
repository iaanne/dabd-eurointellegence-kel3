#!/usr/bin/env bash
# Entrypoint worker Prefect: tunggu API, siapkan work pool, daftarkan deployment,
# lalu jalankan worker. Semua langkah idempoten supaya aman saat restart.
set -euo pipefail

export PREFECT_API_URL="${PREFECT_API_URL:-http://prefect-server:4200/api}"

echo "Menunggu Prefect API di ${PREFECT_API_URL}"
python - <<'PY'
import os
import sys
import time
import urllib.request

url = os.environ["PREFECT_API_URL"].rstrip("/") + "/health"
for _ in range(90):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            if response.status == 200:
                print("Prefect API siap")
                sys.exit(0)
    except Exception:
        pass
    time.sleep(2)

print("Prefect API tidak merespons setelah 180 detik", file=sys.stderr)
sys.exit(1)
PY

if ! prefect work-pool inspect eurogrid-pool >/dev/null 2>&1; then
  echo "Membuat work pool eurogrid-pool"
  prefect work-pool create eurogrid-pool --type process
fi

echo "Mendaftarkan deployment dari prefect.yaml"
prefect deploy --all --prefect-file /app/prefect.yaml

echo "Menjalankan worker"
exec prefect worker start --pool eurogrid-pool --type process
