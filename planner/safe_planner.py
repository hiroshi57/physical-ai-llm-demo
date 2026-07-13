"""クローズドループ安全計画(全機能): 計画 -> 安全検証 -> (危険なら)回避して再計画.

LLMプランナが危険を含むプランを出しても、安全性検証で検出し、回避制約を強めて
自動リプランする。これによりフィジカルAIの「計画→検証→実行」を閉じたループにする。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from simulator.env import Action, GridWorld
from .llm_planner import Planner, PlanningError
from .safety import SafetyReport, SafetyVerifier


@dataclass
class SafePlanResult:
    plan: List[Action]
    safe: bool
    attempts: int
    report: SafetyReport
    replanned: bool = False


class SafePlanner:
    def __init__(self, verifier: SafetyVerifier = None, max_retries: int = 2) -> None:
        self.verifier = verifier or SafetyVerifier()
        self.max_retries = max_retries

    def plan_safe(self, env: GridWorld, instruction: str) -> SafePlanResult:
        # 1回目: 危険回避なし(=LLMが危険を見落とすケースを模擬)
        planner = Planner(avoid_hazards=False)
        plan = planner.plan(env, instruction)
        report = self.verifier.verify(env, plan)
        if report.safe:
            return SafePlanResult(plan, True, 1, report, replanned=False)

        # 2回目以降: 危険回避を有効にして再計画(クローズドループ)
        for attempt in range(2, self.max_retries + 2):
            safe_planner = Planner(avoid_hazards=True)
            try:
                plan = safe_planner.plan(env, instruction)
            except PlanningError:
                break
            report = self.verifier.verify(env, plan)
            if report.safe:
                return SafePlanResult(plan, True, attempt, report, replanned=True)
        return SafePlanResult(plan, False, self.max_retries + 1, report, replanned=True)
