"""フィジカルAI サービスAPI(FastAPI). 計画(安全検証) -> 実行 -> 履歴/レポート. テナント分離.
`uvicorn service.api:app --reload`
"""
from datetime import datetime, timezone

from simulator.env import Action, GridWorld
from simulator import render_grid
from planner import SafePlanner
from executor import ActionExecutor
from .db import ServiceDB
from .report_html import build_html_report

DB = ServiceDB(":memory:")


def default_world() -> GridWorld:
    return GridWorld(width=6, height=6, robot=(0, 0), goal=(5, 5),
                     obstacles={(2, 0), (2, 1), (2, 2)}, hazards={(3, 3), (4, 4)},
                     objects={"箱": (4, 1)})


def _plan_code(a: Action) -> str:
    return a.direction[:1].upper() if a.kind == "move" else a.kind.upper()[:2]


def run_instruction(tenant: str, instruction: str) -> dict:
    env = default_world()
    grid = render_grid(env)
    result = SafePlanner().plan_safe(env, instruction)
    delivered = []
    if result.safe:
        ActionExecutor().execute(env, result.plan)
        delivered = sorted(env.delivered)
    plan_codes = [_plan_code(a) for a in result.plan]
    now = datetime.now(timezone.utc).isoformat()
    run_id = DB.save_run(tenant, instruction, result.safe, result.replanned,
                         result.attempts, delivered, plan_codes, grid, now)
    return {"run_id": run_id, "safe": result.safe, "replanned": result.replanned,
            "attempts": result.attempts, "delivered": delivered, "plan": plan_codes, "grid": grid}


def create_app():  # pragma: no cover
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel

    app = FastAPI(title="Physical AI LLM Demo", version="1.0.0")

    def tenant(x_tenant_id: str = Header(...)) -> str:
        if not x_tenant_id:
            raise HTTPException(401, "tenant required")
        return x_tenant_id

    class RunIn(BaseModel):
        instruction: str = "箱をゴールに運んで"

    @app.post("/v1/run")
    def run(body: RunIn, t: str = Depends(tenant)):
        return run_instruction(t, body.instruction)

    @app.get("/v1/history")
    def history(t: str = Depends(tenant)):
        return {"history": DB.history(t)}

    @app.get("/v1/report/{run_id}", response_class=HTMLResponse)
    def report(run_id: int, t: str = Depends(tenant)):
        run = DB.get_run(t, run_id)
        if run is None:
            raise HTTPException(404, "run not found")
        return build_html_report(run)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


try:  # pragma: no cover
    app = create_app()
except Exception:
    app = None
