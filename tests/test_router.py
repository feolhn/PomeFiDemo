from __future__ import annotations

from pomefi.stock_wiki.router import route_query, resolve_symbol_from_table


def _sample_rows() -> list[dict[str, str]]:
    return [
        {"code": "300750", "name": "宁德时代"},
        {"code": "600519", "name": "贵州茅台"},
    ]


def test_resolve_symbol_from_table_by_code_and_name() -> None:
    assert resolve_symbol_from_table("300750 怎么看", _sample_rows()) == ("300750", "宁德时代")
    assert resolve_symbol_from_table("宁德时代", _sample_rows()) == ("300750", "宁德时代")


def test_route_query_unsupported_scope() -> None:
    route = route_query(question="美股英伟达怎么看", stock_table_loader=_sample_rows)
    assert route["scope"] == "unsupported"
    assert route["reason"] == "unsupported_scope"


def test_route_query_symbol_unresolved() -> None:
    route = route_query(question="这家公司怎么样", stock_table_loader=_sample_rows)
    assert route["status"] == "degraded"
    assert route["reason"] == "symbol_unresolved"


def test_route_query_valid() -> None:
    route = route_query(question="宁德时代怎么看", stock_table_loader=_sample_rows)
    assert route["status"] == "valid"
    assert route["scope"] == "a_share"
    assert route["symbol"] == "300750"
