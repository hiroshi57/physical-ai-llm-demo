"""アクション実行器. 安全性検証を通過したプランのみをシミュレータへ適用する."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from planner.safety import SafetyReport, SafetyVerifier
from simulator.env import Action, ActionResult, GridWorld


class UnsafePlanError(Exception):
    def __init__(self, report: SafetyReport) -> None:
        super().__init__("安全性検証に失敗したためプランを実行しません")
        self.report = report


@dataclass
class ExecStep:
    action: dict
    ok: bool
    message: str


class ActionExecutor:
    def __init__(self, verifier: Optional[SafetyVerifier] = None, log_path: Optional[str] = None) -> None:
        self.verifier = verifier or SafetyVerifier()
        self.log_path = log_path

    def execute(self, env: GridWorld, plan: List[Action], enforce_safety: bool = True) -> List[ExecStep]:
        # 実行前ゲート: 安全性検証(差別化)
        report = self.verifier.verify(env, plan)
        if enforce_safety and not report.safe:
            raise UnsafePlanError(report)

        steps: List[ExecStep] = []
        for action in plan:
            res: ActionResult = env.apply(action)
            step = ExecStep(action.as_dict(), res.ok, res.message)
            steps.append(step)
            self._log(step)
            if not res.ok:
                break
        return steps

    def _log(self, step: ExecStep) -> None:
        if not self.log_path:
            return
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "action": step.action, "ok": step.ok, "message": step.message,
            }, ensure_ascii=False) + "\n")
