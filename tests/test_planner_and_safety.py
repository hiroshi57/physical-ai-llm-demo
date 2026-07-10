import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from simulator.env import Action, GridWorld  # noqa: E402
from planner import Planner, SafetyVerifier, PlanningError  # noqa: E402
from executor import ActionExecutor, UnsafePlanError  # noqa: E402


def _world():
    return GridWorld(width=6, height=6, robot=(0, 0), goal=(5, 5),
                     obstacles={(2, 0), (2, 1), (2, 2)}, hazards={(3, 3), (4, 4)},
                     objects={"箱": (4, 1)})


def test_planner_delivers_box_and_plan_is_safe():
    env = _world()
    plan = Planner().plan(env, "箱をゴールに運んで")
    report = SafetyVerifier().verify(env, plan)
    assert report.safe, report.as_dict()
    assert any(a.kind == "pick" for a in plan)
    assert any(a.kind == "place" for a in plan)


def test_planner_plan_executes_to_delivery():
    env = _world()
    plan = Planner().plan(env, "箱をゴールに運んで")
    ActionExecutor().execute(env, plan)
    assert "箱" in env.delivered
    assert env.robot == env.goal


def test_planner_avoids_obstacles_and_hazards():
    env = _world()
    plan = Planner(avoid_hazards=True).plan(env, "箱をゴールに運んで")
    # プランを辿って危険/障害セルに入らないことを確認
    sim = env.copy()
    for a in plan:
        if a.kind == "move":
            t = sim.target_of(a.direction)
            assert t not in env.obstacles and t not in env.hazards
        sim.apply(a)


def test_safety_detects_hazard_plan():
    env = _world()
    # (0,0)->下3->(0,3)->右3->(3,3)=危険セル
    unsafe = [Action("move", "down")] * 3 + [Action("move", "right")] * 3
    report = SafetyVerifier().verify(env, unsafe)
    assert not report.safe
    assert any(v.kind == "hazard" for v in report.violations)


def test_safety_detects_out_of_bounds_and_collision():
    env = _world()
    report = SafetyVerifier().verify(env, [Action("move", "up")])         # 範囲外
    assert any(v.kind == "out_of_bounds" for v in report.violations)
    env2 = _world()
    rep2 = SafetyVerifier().verify(env2, [Action("move", "right"), Action("move", "right")])  # (2,0)障害物
    assert any(v.kind == "collision" for v in rep2.violations)


def test_safety_detects_invalid_pick():
    env = _world()
    report = SafetyVerifier().verify(env, [Action("pick")])   # 現在地に物体なし
    assert any(v.kind == "precondition" for v in report.violations)


def test_executor_rejects_unsafe_plan():
    env = _world()
    unsafe = [Action("move", "right")] * 3 + [Action("move", "down")] * 3
    with pytest.raises(UnsafePlanError):
        ActionExecutor().execute(env, unsafe)
    # 実環境は変更されていない(実行拒否)
    assert env.robot == (0, 0)


def test_verify_does_not_mutate_env():
    env = _world()
    SafetyVerifier().verify(env, [Action("move", "down"), Action("move", "down")])
    assert env.robot == (0, 0)


def test_planning_error_when_unreachable():
    env = GridWorld(width=3, height=3, robot=(0, 0), goal=(2, 2),
                    obstacles={(1, 0), (0, 1), (1, 1)}, objects={})
    with pytest.raises(PlanningError):
        Planner().plan(env, "ゴールに移動")
