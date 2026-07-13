import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.env import GridWorld
from simulator import render_grid
from planner import SafePlanner, SafetyVerifier, Planner
from executor import ActionExecutor


def _world():
    return GridWorld(width=6, height=6, robot=(0, 0), goal=(5, 5),
                     obstacles={(2, 0), (2, 1), (2, 2)}, hazards={(3, 3), (4, 4)},
                     objects={"箱": (4, 1)})


def _multi_world():
    return GridWorld(width=6, height=6, robot=(0, 0), goal=(5, 5),
                     obstacles={(2, 0), (2, 1)}, hazards={(3, 3)},
                     objects={"箱A": (1, 1), "箱B": (4, 1)})


# --- クローズドループ安全計画 ---
def test_safe_planner_returns_safe_plan():
    env = _world()
    result = SafePlanner().plan_safe(env, "箱をゴールに運んで")
    assert result.safe is True
    # 安全プランは危険/障害に入らない
    report = SafetyVerifier().verify(env, result.plan)
    assert report.safe


def test_safe_planner_replans_when_first_unsafe():
    # 列2は 危険(2,0) と障害(2,1)。最短経路は必ず危険(2,0)を通り、
    # 回避するには下段(2,2)へ迂回するしかない配置(決定的)。
    env = GridWorld(width=5, height=3, robot=(0, 0), goal=(4, 0),
                    obstacles={(2, 1)}, hazards={(2, 0)}, objects={})
    result = SafePlanner().plan_safe(env, "ゴールに移動")
    assert result.safe is True
    assert result.replanned is True     # 危険検出->回避で再計画された
    assert result.attempts >= 2


def test_safe_plan_executes_to_goal():
    env = _world()
    result = SafePlanner().plan_safe(env, "箱をゴールに運んで")
    ActionExecutor().execute(env, result.plan)
    assert "箱" in env.delivered


# --- 複数物体搬送 ---
def test_deliver_all_multiple_objects():
    env = _multi_world()
    plan = Planner().plan_deliver_all(env, ["箱A", "箱B"])
    # 安全性検証を通過
    assert SafetyVerifier().verify(env, plan).safe
    ActionExecutor().execute(env, plan)
    assert env.delivered == {"箱A", "箱B"}


def test_deliver_all_missing_object_raises():
    env = _multi_world()
    import pytest
    with pytest.raises(Exception):
        Planner().plan_deliver_all(env, ["存在しない箱"])


# --- 可視化 ---
def test_render_grid_contains_symbols():
    grid = render_grid(_world())
    assert "R" in grid and "G" in grid and "#" in grid and "!" in grid and "o" in grid
    assert grid.count("\n") == 5    # 6行
