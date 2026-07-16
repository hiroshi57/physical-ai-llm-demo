import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from service.db import ServiceDB  # noqa: E402
from service.report_html import build_html_report  # noqa: E402


def test_run_roundtrip_and_history():
    db = ServiceDB(":memory:")
    rid = db.save_run("t-a", "箱をゴールに運んで", True, False, 1, ["箱"],
                      ["D", "R", "PI"], "R . G", "2026-07-09")
    got = db.get_run("t-a", rid)
    assert got["delivered"] == ["箱"] and got["safe"] is True
    assert len(db.history("t-a")) == 1


def test_tenant_isolation():
    db = ServiceDB(":memory:")
    rid = db.save_run("t-a", "x", True, False, 1, [], [], "grid", "2026-07-09")
    assert db.get_run("t-b", rid) is None
    assert db.history("t-b") == []


def test_html_report_sections():
    run = {"instruction": "箱をゴールに運んで", "safe": True, "replanned": False, "attempts": 1,
           "delivered": ["箱"], "plan": ["D", "R", "PI", "PL"], "grid": "R . #\n. o G"}
    html = build_html_report(run)
    assert "実行レポート" in html and "SAFE" in html and "箱をゴールに運んで" in html
    assert "初期グリッド" in html and "生成プラン" in html


def test_html_report_escapes():
    run = {"instruction": "<b>x</b>", "safe": False, "replanned": True, "attempts": 3,
           "delivered": [], "plan": [], "grid": "<script>"}
    html = build_html_report(run)
    assert "<b>x</b>" not in html and "&lt;b&gt;" in html
    assert "UNSAFE" in html


def test_api_e2e_and_tenant_isolation():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from service.api import create_app
    c = TestClient(create_app())
    ha, hb = {"X-Tenant-Id": "t-a"}, {"X-Tenant-Id": "t-b"}
    res = c.post("/v1/run", json={"instruction": "箱をゴールに運んで"}, headers=ha).json()
    assert res["safe"] is True and "箱" in res["delivered"]
    rid = res["run_id"]
    assert c.get(f"/v1/report/{rid}", headers=hb).status_code == 404    # 越境不可
    r = c.get(f"/v1/report/{rid}", headers=ha)
    assert r.status_code == 200 and "実行レポート" in r.text
    assert len(c.get("/v1/history", headers=ha).json()["history"]) == 1
