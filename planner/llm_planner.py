"""LLM プランナ. 自然言語指示 -> 行動プラン(プリミティブ列)を生成する.

実運用では Claude に planner_prompt.md を与え、行動列を JSON で受け取る。
APIキー無しでも動くよう、ここでは BFS 経路計画によるルールベース代替を実装。
プランナは障害物と危険セルの両方を避けて安全なプランを作る(その上で安全性検証で二重確認)。
"""
from __future__ import annotations

from collections import deque
from typing import List, Optional, Set, Tuple

from simulator.env import DIRS, Action, GridWorld, Pos


def _bfs_path(env: GridWorld, start: Pos, goal: Pos, blocked: Set[Pos]) -> Optional[List[Pos]]:
    if start == goal:
        return [start]
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        for dx, dy in DIRS.values():
            nxt = (cur[0] + dx, cur[1] + dy)
            if not env.in_bounds(nxt) or nxt in blocked or nxt in prev:
                continue
            prev[nxt] = cur
            if nxt == goal:
                path = [nxt]
                while prev[path[-1]] is not None:
                    path.append(prev[path[-1]])
                return list(reversed(path))
            q.append(nxt)
    return None


def _path_to_moves(path: List[Pos]) -> List[Action]:
    moves: List[Action] = []
    rev = {v: k for k, v in DIRS.items()}
    for a, b in zip(path, path[1:]):
        d = (b[0] - a[0], b[1] - a[1])
        moves.append(Action("move", rev[d]))
    return moves


class Planner:
    def __init__(self, avoid_hazards: bool = True) -> None:
        self.avoid_hazards = avoid_hazards

    def _blocked(self, env: GridWorld) -> Set[Pos]:
        blocked = set(env.obstacles)
        if self.avoid_hazards:
            blocked |= env.hazards
        return blocked

    def plan(self, env: GridWorld, instruction: str) -> List[Action]:
        """指示文から行動プランを生成. 例: 「箱をゴールに運んで」."""
        target_obj = self._resolve_object(env, instruction)
        deliver = any(k in instruction for k in ("ゴール", "運", "届け", "置")) or target_obj is not None

        plan: List[Action] = []
        sim = env.copy()
        blocked = self._blocked(env)

        if target_obj is not None:
            # 物体位置まで移動 -> pick
            path = _bfs_path(sim, sim.robot, sim.objects[target_obj], blocked)
            if path is None:
                raise PlanningError(f"'{target_obj}' への経路が見つかりません")
            plan += _path_to_moves(path)
            for m in _path_to_moves(path):
                sim.apply(m)
            plan.append(Action("pick"))
            sim.apply(Action("pick"))

        if deliver:
            path = _bfs_path(sim, sim.robot, sim.goal, blocked)
            if path is None:
                raise PlanningError("ゴールへの経路が見つかりません")
            plan += _path_to_moves(path)
            plan.append(Action("place"))

        if not plan:
            raise PlanningError(f"指示を解釈できません: {instruction}")
        return plan

    def _resolve_object(self, env: GridWorld, instruction: str) -> Optional[str]:
        for name in env.objects:
            if name in instruction:
                return name
        # 別名(箱/ブロック/荷物)を任意の1物体にマップ
        if any(k in instruction for k in ("箱", "ブロック", "荷物", "物体")) and env.objects:
            return next(iter(env.objects))
        return None


class PlanningError(Exception):
    pass
