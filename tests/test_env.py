import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.env import Action, GridWorld  # noqa: E402


def _world():
    return GridWorld(width=3, height=3, robot=(0, 0), goal=(2, 2),
                     obstacles={(1, 0)}, objects={"箱": (0, 1)})


def test_move_ok():
    w = _world()
    assert w.apply(Action("move", "down")).ok
    assert w.robot == (0, 1)


def test_move_into_obstacle_blocked():
    w = _world()
    r = w.apply(Action("move", "right"))   # (1,0) は障害物
    assert not r.ok
    assert w.robot == (0, 0)


def test_move_out_of_bounds_blocked():
    w = _world()
    assert not w.apply(Action("move", "up")).ok


def test_pick_and_place_delivery():
    w = _world()
    w.apply(Action("move", "down"))         # (0,1) 箱の位置
    assert w.apply(Action("pick")).ok
    assert w.holding == "箱"
    # ゴールへ移動して配置
    w.apply(Action("move", "down"))          # (0,2)
    w.apply(Action("move", "right"))         # (1,2)
    w.apply(Action("move", "right"))         # (2,2)=goal
    r = w.apply(Action("place"))
    assert r.ok and "箱" in w.delivered


def test_pick_without_object_fails():
    w = _world()
    assert not w.apply(Action("pick")).ok


def test_copy_is_independent():
    w = _world()
    c = w.copy()
    c.apply(Action("move", "down"))
    assert w.robot == (0, 0)   # 元は不変
