"""デモ(APIキー不要). 自然言語 -> プラン -> 安全性検証 -> 実行. `python demo.py`"""
import os

from simulator.env import Action, GridWorld
from planner import Planner, SafetyVerifier
from executor import ActionExecutor, UnsafePlanError

LOG = os.path.join(os.path.dirname(__file__), "logs", "run.jsonl")


def build_world():
    # 6x6。ロボット(0,0) -> 箱(4,1) -> ゴール(5,5)。障害物と危険セルあり。
    return GridWorld(
        width=6, height=6, robot=(0, 0), goal=(5, 5),
        obstacles={(2, 0), (2, 1), (2, 2)},
        hazards={(3, 3), (4, 4)},
        objects={"箱": (4, 1)},
    )


def render(env):
    for y in range(env.height):
        row = ""
        for x in range(env.width):
            p = (x, y)
            if p == env.robot: row += "R "
            elif p == env.goal: row += "G "
            elif p in env.obstacles: row += "# "
            elif p in env.hazards: row += "! "
            elif p in env.objects.values(): row += "o "
            else: row += ". "
        print("  " + row)


def main():
    env = build_world()
    print("=== 初期状態 (R=ロボット G=ゴール #=障害物 !=危険 o=箱) ===")
    render(env)

    planner = Planner(avoid_hazards=True)
    plan = planner.plan(env, "箱をゴールに運んで")
    print(f"\n=== 生成プラン({len(plan)}手) ===")
    print("  " + " ".join(a.direction[:1].upper() if a.kind == "move" else a.kind.upper()[:2] for a in plan))

    verifier = SafetyVerifier()
    report = verifier.verify(env, plan)
    print(f"\n=== 安全性検証: {'SAFE' if report.safe else 'UNSAFE'} (違反 {len(report.violations)}件) ===")

    executor = ActionExecutor(verifier=verifier, log_path=LOG)
    steps = executor.execute(env, plan)
    print(f"実行 {len(steps)} ステップ完了。納品済み: {env.delivered}")
    print("\n=== 最終状態 ===")
    render(env)

    # 危険セルを横切る「危険なプラン」は実行前に拒否される
    print("\n=== 安全でないプランは拒否される ===")
    env2 = build_world()
    unsafe = [Action("move", "right"), Action("move", "right"), Action("move", "right"),
              Action("move", "down"), Action("move", "down"), Action("move", "down")]  # (3,3)危険へ
    try:
        ActionExecutor(verifier=verifier).execute(env2, unsafe)
    except UnsafePlanError as e:
        print(f"  拒否: {[v.kind for v in e.report.violations]}")


if __name__ == "__main__":
    main()
