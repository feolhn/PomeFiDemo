from __future__ import annotations

from pomefi.assembler import arbitrate_references, assemble_garden_card
from pomefi.protocol import ensure_required_blocks, fallback_response


def test_assemble_garden_card_outputs_valid_contract(sample_result_card_input: dict) -> None:
    card = assemble_garden_card(**sample_result_card_input)

    assert set(card.keys()) == {"data", "metadata", "quality_status"}
    assert card["quality_status"] == "valid"
    block_types = [block["type"] for block in card["data"]["blocks"]]
    assert "yields" in block_types
    assert "pests" in block_types
    assert "pruning" in block_types
    assert "flowering" in block_types
    assert "soil" in block_types
    assert card["data"]["references"]
    assert card["metadata"]["degrade_reason"] is None


def test_arbitrate_references_prefers_newer_timestamp_then_source() -> None:
    references = [
        {"id": "older", "title": "older", "source": "新华社", "published_at": "2026-02-26T08:00:00+08:00", "url": None, "kind": "web_search"},
        {"id": "newer", "title": "newer", "source": "AkShare", "published_at": "2026-02-27T08:00:00+08:00", "url": None, "kind": "akshare"},
        {"id": "official", "title": "official", "source": "上交所公告", "published_at": "2026-02-27T08:00:00+08:00", "url": None, "kind": "web_search"},
    ]

    ordered = arbitrate_references(references)

    assert ordered[0]["id"] == "official"
    assert ordered[1]["id"] == "newer"
    assert ordered[2]["id"] == "older"


def test_assemble_garden_card_degrades_on_tool_error(sample_result_card_input: dict) -> None:
    trace = sample_result_card_input["trace"]
    trace["tool_events"].append(
        {
            "tool_name": "web_search",
            "tool_call_id": "call_web_error",
            "source": "formula",
            "formula_uri": "moonshot/web-search:latest",
            "arguments_text": "{}",
            "arguments_dict": {},
            "jsonable_ok": None,
            "local_context_keys": [],
            "tool_content": '{"error":"boom"}',
            "tool_content_preview": '{"error":"boom"}',
        }
    )

    card = assemble_garden_card(**sample_result_card_input)

    assert card["quality_status"] == "degraded"
    assert card["metadata"]["degrade_reason"] == "formula_error"


def test_fallback_response_returns_minimal_shell() -> None:
    result = fallback_response(
        question="宁德时代怎么看",
        model="kimi-k2.5",
        degrade_reason="assembler_error",
    )

    assert result["quality_status"] == "degraded"
    assert result["metadata"]["degrade_reason"] == "assembler_error"
    assert [block["type"] for block in result["data"]["blocks"]] == ["yields", "pests", "pruning"]


def test_ensure_required_blocks_backfills_missing_types() -> None:
    blocks = ensure_required_blocks(
        [
            {
                "id": "soil_1",
                "type": "soil",
                "title": "土壤",
                "summary": "summary",
                "bullets": ["b1"],
                "metric_refs": [],
                "reference_ids": [],
                "chart_ids": [],
            }
        ]
    )

    assert [block["type"] for block in blocks] == ["soil", "yields", "pests", "pruning"]
