"""测试 API #3 GET /assets（聚合汇总 + 最佳/最差）。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

AAPL = {
    "symbol": "AAPL", "name": "Apple Inc.", "category": "美股", "currency": "USD",
    "quantity": 10, "price": 200.0, "exchange_rate_to_cny": 7.0,
    "date": "2026-04-01",
}
MAOTAI = {
    "symbol": "600519", "name": "贵州茅台", "category": "中概股", "currency": "CNY",
    "quantity": 2, "price": 1500.0, "exchange_rate_to_cny": 1.0,
    "date": "2026-04-01",
}


# ============================================================
# 空状态
# ============================================================
def test_list_assets_empty(client: TestClient) -> None:
    resp = client.get("/api/assets")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["assets"] == []
    assert data["summary"]["total_initial_investment_cny"] == 0
    assert data["summary"]["total_current_value_cny"] == 0
    assert data["summary"]["best_asset"] is None
    assert data["summary"]["worst_asset"] is None


# ============================================================
# 单资产：聚合字段完整性
# ============================================================
def test_list_assets_single_usd(client: TestClient) -> None:
    assert client.post("/api/assets", json=AAPL).status_code == 201
    resp = client.get("/api/assets")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["assets"]) == 1
    item = data["assets"][0]
    assert item["symbol"] == "AAPL"
    assert item["is_active"] is True
    assert item["quantity"] == 10
    assert item["current_price_original"] == 200.0  # POST /assets 写入的首笔价格
    assert item["exchange_rate_to_cny"] == pytest.approx(7.0)
    assert item["current_value_cny"] == pytest.approx(10 * 200 * 7.0)
    assert item["cost_price_original"] == 200.0
    assert item["cumulative_return_rate"] == pytest.approx(0.0)
    # position_ratio 唯一资产应为 1.0
    assert item["position_ratio"] == pytest.approx(1.0)

    s = data["summary"]
    assert s["total_initial_investment_cny"] == pytest.approx(14000)
    assert s["total_current_value_cny"] == pytest.approx(14000)
    assert s["total_profit_loss_cny"] == pytest.approx(0.0)


# ============================================================
# 多资产：position_ratio + best/worst
# ============================================================
def test_list_assets_multi_position_ratio(client: TestClient) -> None:
    assert client.post("/api/assets", json=AAPL).status_code == 201     # 14000 CNY
    assert client.post("/api/assets", json=MAOTAI).status_code == 201   # 3000 CNY

    resp = client.get("/api/assets")
    data = resp.json()
    items_by_symbol = {i["symbol"]: i for i in data["assets"]}
    assert items_by_symbol["AAPL"]["position_ratio"] == pytest.approx(14000 / 17000)
    assert items_by_symbol["600519"]["position_ratio"] == pytest.approx(3000 / 17000)
    assert data["summary"]["total_current_value_cny"] == pytest.approx(17000)


# ============================================================
# include_closed 参数 + 已关闭字段 null
# ============================================================
def test_list_assets_include_closed(client: TestClient) -> None:
    r_add = client.post("/api/assets", json=AAPL)
    asset_id = r_add.json()["asset_id"]
    assert client.request("DELETE", f"/api/assets/{asset_id}").status_code == 204

    # 默认不含已关闭
    r_default = client.get("/api/assets")
    assert r_default.json()["assets"] == []

    # include_closed=true 返回，但所有数值字段 null
    r_all = client.get("/api/assets", params={"include_closed": "true"})
    assets = r_all.json()["assets"]
    assert len(assets) == 1
    closed = assets[0]
    assert closed["is_active"] is False
    assert closed["quantity"] is None
    assert closed["current_price_original"] is None
    assert closed["current_value_cny"] is None
    assert closed["monthly_return_rate"] is None
    assert closed["position_ratio"] is None


# ============================================================
# best/worst：两个资产 monthly_return_rate 不同
# ============================================================
def test_best_and_worst_when_only_one_active(client: TestClient) -> None:
    """单资产时 best 和 worst 应指向同一资产。"""
    assert client.post("/api/assets", json=AAPL).status_code == 201
    s = client.get("/api/assets").json()["summary"]
    # AAPL POST 后 current_price == 买入价 → monthly_return_rate 也是 0（同月）
    assert s["best_asset"] is not None
    assert s["worst_asset"] is not None
    assert s["best_asset"]["symbol"] == s["worst_asset"]["symbol"] == "AAPL"
