"""プラン安全性検証レイヤ(本デモの差別化).

LLM が生成したプランを、実行(実機/シミュレータ適用)の前に検証する独立レイヤ。
プランをシミュレータのコピー上でドライ実行し、以下の違反を検出する:
  - 範囲外への移動
  - 障害物との衝突
  - 危険セル(hazard)への進入
  - 不正な pick/place(保持状態の矛盾)
  - プラン長の上限超過
違反があれば unsafe と判定し、実行させない。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from simulator.env import Action, GridWorld


@dataclass
class Violation:
    step: int
    kind: str
    detail: str

    def as_dict(self):
        return {"step": self.step, "kind": self.kind, "detail": self.detail}


@dataclass
class SafetyReport:
    safe: bool
    violations: List[Violation] = field(default_factory=list)

    def as_dict(self):
        return {"safe": self.safe, "violations": [v.as_dict() for v in self.violations]}


class SafetyVerifier:
    def __init__(self, max_steps: int = 100) -> None:
        self.max_steps = max_steps

    def verify(self, env: GridWorld, plan: List[Action]) -> SafetyReport:
        violations: List[Violation] = []
        if len(plan) > self.max_steps:
            violations.append(Violation(-1, "too_long",
                                        f"プラン長 {len(plan)} が上限 {self.max_steps} を超過"))
        sim = env.copy()  # 実環境は変更しない(ドライ実行)
        for i, action in enumerate(plan):
            if action.kind == "move":
                target = sim.target_of(action.direction) if action.direction in ("up", "down", "left", "right") else None
                if target is None:
                    violations.append(Violation(i, "invalid_action", f"不明な方向: {action.direction}"))
                    continue
                if not sim.in_bounds(target):
                    violations.append(Violation(i, "out_of_bounds", f"範囲外 {target}"))
                    continue
                if target in sim.obstacles:
                    violations.append(Violation(i, "collision", f"障害物 {target} に衝突"))
                    continue
                if target in sim.hazards:
                    violations.append(Violation(i, "hazard", f"危険セル {target} に進入"))
                    # hazard でも物理的には進めるのでドライ実行は継続
                sim.robot = target
            else:
                ok, reason = sim.can_apply(action)
                if not ok:
                    violations.append(Violation(i, "precondition", reason))
                else:
                    sim.apply(action)
        return SafetyReport(safe=(len(violations) == 0), violations=violations)
