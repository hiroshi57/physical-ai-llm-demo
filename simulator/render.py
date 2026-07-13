"""グリッド可視化(全機能). 環境をASCIIで描画する共通モジュール."""
from __future__ import annotations

from .env import GridWorld

LEGEND = "R=ロボット G=ゴール #=障害物 !=危険 o=物体"


def render_grid(env: GridWorld) -> str:
    rows = []
    for y in range(env.height):
        cells = []
        for x in range(env.width):
            p = (x, y)
            if p == env.robot:
                cells.append("R")
            elif p == env.goal:
                cells.append("G")
            elif p in env.obstacles:
                cells.append("#")
            elif p in env.hazards:
                cells.append("!")
            elif p in env.objects.values():
                cells.append("o")
            else:
                cells.append(".")
        rows.append(" ".join(cells))
    return "\n".join(rows)
