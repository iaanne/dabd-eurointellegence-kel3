from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import respx
from httpx import Response

from eurogrid.config import load_settings
from eurogrid.ingest import ingest_entsoe
from eurogrid.sources import entsoe

FIXTURES = Path(__file__).parent / "fixtures"
URL = "https://web-api.tp.entsoe.eu/api"


def _xml() -> str:
    return (FIXTURES / "entsoe_actual_load.xml").read_text(encoding="utf-8")


def test_build_params_memakai_periode_utc() -> None:
    params = entsoe.build_params(
        security_token="rahasia",
        dataset="actual_load",
        bidding_zone="10Y1001A1001A82H",
        start="2026-11-03",
        end="2026-11-09",
    )

    assert params["documentType"] == "A65"
    assert params["processType"] == "A16"
    assert params["outBiddingZone_Domain"] == "10Y1001A1001A82H"
    assert params["periodStart"] == "202611030000"
    assert params["periodEnd"] == "202611100000"


def test_build_params_menolak_dataset_lain() -> None:
    with pytest.raises(ValueError):
        entsoe.build_params(
            security_token="rahasia",
            dataset="harga",
            bidding_zone="10Y1001A1001A82H",
            start="2026-11-03",
            end="2026-11-03",
        )


def test_parse_document_menghasilkan_tabel_panjang() -> None:
    envelope = entsoe.parse_document(_xml())
    frame = entsoe.to_long_frame(envelope, dataset="actual_load")

    assert envelope["document_type"] == "A65"
    assert envelope["resolution"] == "PT15M"
    assert envelope["unit"] == "MAW"
    assert len(frame) == 4
    assert frame["timestamp_utc"].iloc[0].isoformat() == "2026-11-03T00:00:00+00:00"
    assert frame["timestamp_utc"].iloc[1].isoformat() == "2026-11-03T00:15:00+00:00"
    assert frame["value"].iloc[0] == pytest.approx(48871.07331)
    assert frame["series_id"].unique().tolist() == ["1"]
    assert frame["bidding_zone"].unique().tolist() == ["10Y1001A1001A82H"]


def test_envelope_tidak_memuat_field_volatil() -> None:
    pertama = entsoe.parse_document(_xml())
    kedua = entsoe.parse_document(_xml().replace("0722f236", "abcdef12"))

    assert "document" not in pertama
    assert pertama == kedua


def test_ingest_entsoe_menulis_batch_dan_menyunting_token(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("EUROGRID_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENTSOE_API_TOKEN", "token-uji")

    def panggil() -> dict:
        with respx.mock(assert_all_called=True) as mock:
            mock.get(URL).mock(return_value=Response(200, text=_xml()))
            return ingest_entsoe(
                start="2026-11-03",
                end="2026-11-03",
                settings=replace(load_settings(), data_dir=tmp_path),
            )

    pertama = panggil()
    assert pertama["created"] is True
    assert pertama["row_count"] == 4

    metadata_path = next(tmp_path.rglob("metadata.json"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["source"] == "entsoe"
    assert metadata["request"]["params"]["securityToken"] == "***"
    assert "token-uji" not in metadata_path.read_text(encoding="utf-8")

    kedua = panggil()
    assert kedua["batch_id"] == pertama["batch_id"]
    assert kedua["created"] is False
    assert len(list(tmp_path.rglob("data.parquet"))) == 1


def test_ingest_entsoe_butuh_token(tmp_path: Path) -> None:
    settings = replace(
        load_settings(), data_dir=tmp_path, entsoe_api_token=None
    )
    with pytest.raises(ValueError):
        ingest_entsoe(
            start="2026-11-03",
            end="2026-11-03",
            settings=settings,
        )