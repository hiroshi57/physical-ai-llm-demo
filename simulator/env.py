"""簡易シミュレータ: 2Dグリッドの移動ロボット(実機不要).

セル種別:
  - obstacle: 物理的に進入不可(衝突)
  - hazard  : 物理的には進入可能だが「危険」。安全性検証レイヤが拒否する対象
ロボットは move(4方向) / pick / place を行える。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

Pos = Tuple[int, int]

DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


@dataclass(frozen=True)
class Action:
    kind: str                 # move / pick / place
    direction: str = ""       # move の場合のみ

    def as_dict(self):
        return {"kind": self.kind, "direction": self.direction}


@dataclass
class ActionResult:
    ok: bool
    message: str


@dataclass
class GridWorld:
    width: int
    height: int
    robot: Pos
    goal: Pos
    obstacles: Set[Pos] = field(default_factory=set)
    hazards: Set[Pos] = field(default_factory=set)
    objects: Dict[str, Pos] = field(default_factory=dict)   # name -> pos
    holding: Optional[str] = None
    delivered: Set[str] = field(default_factory=set)

    def copy(self) -> "GridWorld":
        return GridWorld(
            width=self.width, height=self.height, robot=self.robot, goal=self.goal,
            obstacles=set(self.obstacles), hazards=set(self.hazards),
            objects=dict(self.objects), holding=self.holding, delivered=set(self.delivered),
        )

    def in_bounds(self, p: Pos) -> bool:
        return 0 <= p[0] < self.width and 0 <= p[1] < self.height

    def target_of(self, direction: str) -> Pos:
        d = DIRS[direction]
        return (self.robot[0] + d[0], self.robot[1] + d[1])

    def can_apply(self, action: Action) -> Tuple[bool, str]:
        if action.kind == "move":
            if action.direction not in DIRS:
                return False, f"不明な方向: {action.direction}"
            t = self.target_of(action.direction)
            if not self.in_bounds(t):
                return False, f"範囲外への移動: {t}"
            if t in self.obstacles:
                return False, f"障害物との衝突: {t}"
            return True, ""
        if action.kind == "pick":
            if self.holding is not None:
                return False, f"すでに '{self.holding}' を保持中"
            here = [n for n, p in self.objects.items() if p == self.robot]
            if not here:
                return False, "現在地に拾える物体がない"
            return True, ""
        if action.kind == "place":
            if self.holding is None:
                return False, "保持している物体がない"
            return True, ""
        return False, f"不明なアクション: {action.kind}"

    def apply(self, action: Action) -> ActionResult:
        ok, reason = self.can_apply(action)
        if not ok:
            return ActionResult(False, reason)
        if action.kind == "move":
            self.robot = self.target_of(action.direction)
            return ActionResult(True, f"移動 -> {self.robot}")
        if action.kind == "pick":
            name = next(n for n, p in self.objects.items() if p == self.robot)
            self.holding = name
            del self.objects[name]
            return ActionResult(True, f"'{name}' を把持")
        if action.kind == "place":
            name = self.holding
            self.objects[name] = self.robot
            self.holding = None
            if self.robot == self.goal:
                self.delivered.add(name)
                return ActionResult(True, f"'{name}' をゴールに配置(納品)")
            return ActionResult(True, f"'{name}' を {self.robot} に配置")
        return ActionResult(False, "unreachable")
