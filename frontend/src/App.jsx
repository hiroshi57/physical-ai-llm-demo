import React, { useState } from "react";
import PlanViewer from "./screens/PlanViewer.jsx";
import RunHistory from "./screens/RunHistory.jsx";
import { run, history, reportUrl } from "./api.js";

const TENANT = "demo-tenant";
const DEMO_RESULT = {
  run_id: 1, safe: true, replanned: false, attempts: 1, delivered: ["箱"],
  plan: ["D", "D", "D", "D", "D", "R", "R", "R", "R", "R", "U", "U", "U", "U", "PI", "D", "D", "R", "D", "D", "PL"],
  grid: "R . # . . .\n. . # . o .\n. . # . . .\n. . . ! . .\n. . . . ! .\n. . . . . G",
};

export default function App() {
  const [tab, setTab] = useState("plan");
  const [result, setResult] = useState(DEMO_RESULT);
  const [runs, setRuns] = useState([]);
  const [busy, setBusy] = useState(false);

  const doRun = async (instruction) => {
    setBusy(true);
    try {
      const res = await run(TENANT, instruction);
      setResult(res);
      setRuns((await history(TENANT)).history || []);
    } catch (e) {
      alert("バックエンド未起動の可能性: " + e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="wrap">
      <h1>フィジカルAI × LLM デモ</h1>
      <nav>
        <button onClick={() => setTab("plan")} disabled={tab === "plan"}>プラン可視化</button>
        <button onClick={() => setTab("history")} disabled={tab === "history"}>実行履歴</button>
      </nav>
      {tab === "plan"
        ? <PlanViewer onRun={doRun} result={result} busy={busy} />
        : <RunHistory runs={runs} onOpenReport={(id) => window.open(reportUrl(id), "_blank")} />}
    </div>
  );
}
