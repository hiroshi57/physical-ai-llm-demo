import React, { useState } from "react";

// プラン可視化: 指示 -> グリッド + 生成プラン + 安全性検証。
export default function PlanViewer({ onRun, result, busy }) {
  const [instruction, setInstruction] = useState("箱をゴールに運んで");
  return (
    <div className="card">
      <h2>計画 → 安全性検証 → 実行</h2>
      <input style={{ width: "100%" }} value={instruction}
        onChange={(e) => setInstruction(e.target.value)} />
      <button className="primary" disabled={busy} onClick={() => onRun(instruction)}>
        {busy ? "計画中..." : "実行"}
      </button>
      {result && (
        <div className="result">
          <p>安全性: <b className={result.safe ? "safe" : "unsafe"}>
            {result.safe ? "SAFE ✓" : "UNSAFE ✗"}</b>
            {result.replanned && "（危険検出→回避で再計画）"} / 試行{result.attempts}回</p>
          <pre className="grid">{result.grid}</pre>
          <p>プラン（{result.plan.length}手）: <code>{result.plan.join(" ")}</code></p>
          <p>納品済み: {result.delivered.join("、") || "なし"}</p>
        </div>
      )}
    </div>
  );
}
