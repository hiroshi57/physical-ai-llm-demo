"""形式的安全仕様エンジン(尖った武器).

安全性を「宣言的な不変条件(invariant)」として記述し、任意のプランを実行前に検証する
独立セーフティ層。どのプランナ(LLM/古典)にも後付けで挿せる。違反時は反例(どのステップで
どの不変条件が破れたか)を返す。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from simulator.env import Action, GridWorld

# 不変条件 = (名前, 述語). 述語は「その状態が安全か」を返す。
Invariant = Callable[[GridWorld], bool]


@dataclass
class SpecViolation:
    step: int
    invariant: str
    detail: str

    def as_dict(self):
        return {"step": self.step, "invariant": self.invariant, "detail": self.detail}


@dataclass
class SpecResult:
    satisfied: bool
    violations: List[SpecViolation] = field(default_factory=list)

    def as_dict(self):
        return {"satisfied": self.satisfied, "violations": [v.as_dict() for v in self.violations]}


# --- 標準の不変条件ライブラリ ---
def never_enter_hazard(env: GridWorld) -> bool:
    return env.robot not in env.hazards


def never_out_of_bounds(env: GridWorld) -> bool:
    return env.in_bounds(env.robot)


def never_on_obstacle(env: GridWorld) -> bool:
    return env.robot not in env.obstacles


def max_steps_invariant(limit: int) -> Invariant:
    state = {"n": 0}

    def inv(env: GridWorld) -> bool:
        state["n"] += 1
        return state["n"] <= limit
    return inv


DEFAULT_SPEC = {
    "危険セル進入禁止": never_enter_hazard,
    "範囲外進入禁止": never_out_of_bounds,
    "障害物進入禁止": never_on_obstacle,
}


class SafetySpec:
    """宣言的不変条件の集合を、プランのドライ実行で検証する."""

    def __init__(self, invariants: dict = None) -> None:
        self.invariants = invariants or dict(DEFAULT_SPEC)

    def verify(self, env: GridWorld, plan: List[Action]) -> SpecResult:
        sim = env.copy()   # 実環境は変更しない
        violations: List[SpecViolation] = []
        for i, action in enumerate(plan):
            # 物理的に不可能な move は状態を進めない(=衝突/範囲外はここでは検出しspecでも判定)
            if action.kind == "move" and action.direction in ("up", "down", "left", "right"):
                target = sim.target_of(action.direction)
                if sim.in_bounds(target) and target not in sim.obstacles:
                    sim.robot = target
                else:
                    # 実行不能な動作: 該当不変条件で反例化
                    name = "範囲外進入禁止" if not sim.in_bounds(target) else "障害物進入禁止"
                    if name in self.invariants:
                        violations.append(SpecViolation(i, name, f"ステップ{i}: {action.direction}先 {target}"))
                    continue
            else:
                sim.apply(action)
            # 各不変条件を現在状態で評価
            for name, inv in self.invariants.items():
                if not inv(sim):
                    violations.append(SpecViolation(i, name, f"ステップ{i}後に不変条件 '{name}' 違反"))
        return SpecResult(satisfied=len(violations) == 0, violations=violations)
