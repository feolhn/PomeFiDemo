from __future__ import annotations

from datetime import datetime
import json
from types import SimpleNamespace

import pytest

import skill_engine


def _sum_pct(mapping: dict[str, str]) -> float:
    return sum(float(v.replace("%", "")) for v in mapping.values())


def test_trend_follower_assertions() -> None:
    result = skill_engine.generate_skill_card("trend_follower", "300750")
    data = result["data"]

    assert result["quality_status"] in {"valid", "degraded", "error"}
    assert isinstance(data["upside_reasons"], list)
    assert len(data["upside_reasons"]) > 0

    for item in data["news_timeline"]:
        assert "date" in item
        datetime.fromisoformat(item["date"])


def test_fund_diagnostic_assertions() -> None:
    result = skill_engine.generate_skill_card("fund_diagnostic", "001410")
    data = result["data"]

    assert len(data["top10_holdings"]) == 10
    assert data["industry_concentration"]["breakdown"]


def test_stock_diagnostic_assertions() -> None:
    input_codes = ["600519", "002594", "600036", "601012", "601318"]
    result = skill_engine.generate_skill_card("stock_diagnostic", input_codes)
    data = result["data"]

    industry_sum = _sum_pct(data["industry_concentration"]["breakdown"])
    cap_sum = _sum_pct(data["market_cap_style"]["cap_breakdown"])

    assert industry_sum == pytest.approx(100.0, abs=0.5)
    assert cap_sum == pytest.approx(100.0, abs=0.5)

    pe_vals = [x["pe"] for x in data["stocks"] if isinstance(x.get("pe"), (int, float))]
    if pe_vals:
        assert data["pe_mean"] == pytest.approx(sum(pe_vals) / len(pe_vals), abs=0.01)


def test_common_contract_fields() -> None:
    result = skill_engine.generate_skill_card("trend_follower", "300750")

    assert "metadata" in result
    assert "generated_at" in result["metadata"]
    assert "data_source" in result["metadata"]
    assert "quality_status" in result
    assert "disclaimer" in result["data"]


def test_degraded_reason_logged(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def fail_ak(*_args, **_kwargs):
        return {}, False

    monkeypatch.setattr(skill_engine, "_fetch_akshare_with_fallback", fail_ak)

    with caplog.at_level("WARNING"):
        result = skill_engine.generate_skill_card("trend_follower", "300750")

    assert result["quality_status"] in {"degraded", "error"}
    assert "degraded_reason=akshare_failed" in caplog.text


def test_prompt_context_trend_is_slimmed_and_limited() -> None:
    # Build a large fake raw payload and ensure context is heavily reduced.
    ak_data = {
        "symbol": "300750",
        "name": "宁德时代",
        "industry": "动力电池",
        "prices": [{"date": f"2026-01-{(i % 30) + 1:02d}", "close": 100 + i} for i in range(200)],
        "current_pe": 32.4,
        "pe_percentile": 62.0,
        "debug_blob": "x" * 5000,
    }
    raw_chars = len(json.dumps(ak_data, ensure_ascii=False))

    ctx = skill_engine._build_prompt_context("trend_follower", ak_data)
    trimmed, _ = skill_engine._apply_prompt_context_budget("trend_follower", ctx, max_chars=800)

    assert "prices" not in ctx
    assert len(ctx["recent_prices"]) <= 20
    assert "debug_blob" not in ctx
    assert len(json.dumps(trimmed, ensure_ascii=False)) <= 800
    assert len(json.dumps(ctx, ensure_ascii=False)) < raw_chars * 0.5


def test_prompt_context_fund_whitelist_only() -> None:
    ak_data = skill_engine._sample_ak_data("fund_diagnostic", {"raw": "001410", "symbol": "SZ001410"})
    ctx = skill_engine._build_prompt_context("fund_diagnostic", ak_data)
    assert set(ctx.keys()) == {"fund_code", "top10_holdings", "industry_top5", "style_ratio"}
    assert len(ctx["top10_holdings"]) <= 10
    assert len(ctx["industry_top5"]) <= 5


def test_prompt_context_stock_aggregate_and_buckets() -> None:
    ak_data = skill_engine._sample_ak_data(
        "stock_diagnostic",
        [
            {"raw": "600519", "symbol": "SH600519"},
            {"raw": "002594", "symbol": "SZ002594"},
            {"raw": "600036", "symbol": "SH600036"},
            {"raw": "601012", "symbol": "SH601012"},
            {"raw": "601318", "symbol": "SH601318"},
        ],
    )
    ctx = skill_engine._build_prompt_context("stock_diagnostic", ak_data)
    assert "aggregate" in ctx
    assert "per_stock_summary" in ctx
    assert len(ctx["per_stock_summary"]) == 5
    for row in ctx["per_stock_summary"]:
        assert set(row.keys()) == {"code", "industry", "market_cap_bucket", "pe_bucket", "market_cap", "pe"}


def test_stream_success_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill_engine, "_resolve_kimi_config", lambda: ("sk-test", "https://api.moonshot.cn/v1", "kimi-k2.5"))

    class FakeStreamClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    assert kwargs.get("stream") is True
                    chunks = [
                        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='{"upside_reasons":["a"],'))]),
                        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='"theme_position":{"level":"x","explanation":"y"}}'))]),
                    ]
                    return iter(chunks)

    monkeypatch.setattr(skill_engine, "OpenAI", lambda **kwargs: FakeStreamClient())

    parsed, ok, used_fallback = skill_engine._stream_kimi_response("{}", stream_callback=None)
    assert ok is True
    assert used_fallback is False
    assert parsed["upside_reasons"] == ["a"]


def test_stream_failure_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill_engine, "_resolve_kimi_config", lambda: ("sk-test", "https://api.moonshot.cn/v1", "kimi-k2.5"))

    class BoomClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    raise RuntimeError("stream failed")

    monkeypatch.setattr(skill_engine, "OpenAI", lambda **kwargs: BoomClient())
    monkeypatch.setattr(skill_engine, "_safe_call_and_parse_kimi", lambda prompt: ({"fallback": True}, True))

    parsed, ok, used_fallback = skill_engine._stream_kimi_response("{}", stream_callback=None)
    assert ok is True
    assert used_fallback is True
    assert parsed["fallback"] is True
