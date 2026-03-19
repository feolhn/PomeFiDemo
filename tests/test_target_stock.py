from __future__ import annotations

import json

import pytest

from scripts import target_stock


def test_load_target_stock_reads_symbol_and_company_name(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "target_stock.json"
    config_path.write_text(json.dumps({"symbol": "002594", "company_name": "比亚迪"}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(target_stock, "TARGET_STOCK_PATH", config_path)

    assert target_stock.load_target_stock() == ("002594", "比亚迪")


def test_load_target_stock_requires_both_fields(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "target_stock.json"
    config_path.write_text(json.dumps({"symbol": "002594"}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(target_stock, "TARGET_STOCK_PATH", config_path)

    with pytest.raises(RuntimeError, match="target_stock config invalid"):
        target_stock.load_target_stock()
