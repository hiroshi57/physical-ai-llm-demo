import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.env import Action, GridWorld  # noqa: E402
from planner import SafetySpec, max_steps_invariant, never_enter_hazard  # noqa: E402


def _world():
    return GridWorld(width=5, height=3, robot=(0, 0), goal=(4, 0),
                     obstacles={(2, 1)}, hazards={(2, 0)}, objects={})


def test_safe_plan_satisfies_spec():
    env = _world()
    # 危険(2,0)と障害(2,1)を避け、列2は最下段(2,2)で横断してから上がる
    plan = [Action("move", "down"), Action("move", "down"),
            Action("move", "right"), Action("move", "right"), Action("move", "right"),
            Action("move", "up"), Action("move", "up"),
            Action("move", "right")]
    r = SafetySpec().verify(env, plan)
    assert r.satisfied is True


def test_hazard_entry_produces_counterexample():
    env = _world()
    # 直進すると(2,0)危険へ
    plan = [Action("move", "right"), Action("move", "right")]
    r = SafetySpec().verify(env, plan)
    assert r.satisfied is False
    assert any(v.invariant == "危険セル進入禁止" for v in r.violations)
    # 反例はステップ番号を含む
    assert r.violations[0].step >= 0


def test_out_of_bounds_counterexample():
    env = _world()
    r = SafetySpec().verify(env, [Action("move", "up")])   # (0,-1) 範囲外
    assert r.satisfied is False
    assert any(v.invariant == "範囲外進入禁止" for v in r.violations)


def test_custom_invariant_max_steps():
    env = _world()
    spec = SafetySpec({"最大ステップ数": max_steps_invariant(2)})
    # 範囲内で有効な3手(右3=(1,0),(2,0),(3,0))。3手目で上限2を超過
    r = spec.verify(env, [Action("move", "right")] * 3)
    assert r.satisfied is False


def test_pluggable_single_invariant():
    env = _world()
    spec = SafetySpec({"危険セル進入禁止": never_enter_hazard})
    # 範囲外は無視、危険のみ検証(独立SDKとして任意の不変条件だけ挿せる)
    r = spec.verify(env, [Action("move", "right"), Action("move", "right")])
    assert any(v.invariant == "危険セル進入禁止" for v in r.violations)


def test_verify_does_not_mutate_env():
    env = _world()
    SafetySpec().verify(env, [Action("move", "down"), Action("move", "down")])
    assert env.robot == (0, 0)
