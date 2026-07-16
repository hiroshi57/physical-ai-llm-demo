"""実行 HTMLレポート(標準ライブラリのみ). グリッド + プラン + 安全性."""
from __future__ import annotations

import html
from typing import Dict


def build_html_report(run: Dict) -> str:
    grid = html.escape(run["grid"])
    plan = " ".join(html.escape(p) for p in run["plan"])
    delivered = "、".join(html.escape(d) for d in run["delivered"]) or "なし"
    safe_badge = "SAFE ✓" if run["safe"] else "UNSAFE ✗"
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<title>フィジカルAI 実行レポート</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;color:#1a1a2e}}
h1{{color:#2f855a}} pre{{background:#f0f4f0;padding:12px;border-radius:8px;font-size:18px;line-height:1.4}}
.badge{{padding:4px 10px;border-radius:8px;color:#fff;background:{'#2f855a' if run['safe'] else '#c0392b'}}}</style></head><body>
<h1>フィジカルAI 実行レポート</h1>
<p>指示: <b>{html.escape(run["instruction"])}</b></p>
<p>安全性検証: <span class="badge">{safe_badge}</span>
   {'（危険検出→回避で再計画）' if run["replanned"] else ''} / 試行 {run["attempts"]}回</p>
<h2>初期グリッド (R=ロボット G=ゴール #=障害物 !=危険 o=物体)</h2>
<pre>{grid}</pre>
<h2>生成プラン ({len(run["plan"])}手)</h2>
<pre>{plan}</pre>
<p>納品済み: {delivered}</p>
</body></html>"""
