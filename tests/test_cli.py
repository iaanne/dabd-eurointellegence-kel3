from __future__ import annotations

import json
from pathlib import Path

import respx
from httpx import Response

from eurogrid.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_energy_charts_menulis_bronze(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("EUROGRID_DATA_DIR", str(tmp_path))
    payload = json.loads(
        (FIXTURES / "energy_charts_public_power.json").read_text(encoding="utf-8")
    )

    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.energy-charts.info/v2/public_power").mock(
            return_value=Response(200, json=payload)
        )
        exit_code = main(
            [
                "ingest-energy-charts",
                "--dataset",
                "public_power",
                "--country",
                "de",
                "--start",
                "2026-11-06",
                "--end",
                "2026-11-06",
            ]
        )

    assert exit_code == 0
    parquet_files = list(tmp_path.rglob("data.parquet"))
    assert len(parquet_files) == 1
    metadata = json.loads(
        (parquet_files[0].parent / "metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["source"] == "energy_charts"
    assert metadata["partition"] == {"country": "de"}