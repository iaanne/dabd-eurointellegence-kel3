from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def test_deployment_bronze_daily() -> None:
    konfigurasi = yaml.safe_load((ROOT / "prefect.yaml").read_text(encoding="utf-8"))
    deployments = konfigurasi["deployments"]

    assert len(deployments) == 1
    deployment = deployments[0]
    assert deployment["name"] == "production"
    assert deployment["work_pool"]["name"] == "eurogrid-pool"
    assert deployment["parameters"]["days"] == 7

    jadwal = deployment["schedules"][0]
    assert jadwal["cron"] == "0 5 * * *"
    assert jadwal["timezone"] == "Europe/Berlin"
    assert jadwal["active"] is True


def test_entrypoint_deployment_ada() -> None:
    konfigurasi = yaml.safe_load((ROOT / "prefect.yaml").read_text(encoding="utf-8"))
    berkas, fungsi = konfigurasi["deployments"][0]["entrypoint"].split(":")

    path = ROOT / berkas
    assert path.is_file()
    assert f"def {fungsi}(" in path.read_text(encoding="utf-8")
