import React from "react";

// 実行履歴: 過去の指示・安全性・納品結果。
export default function RunHistory({ runs, onOpenReport }) {
  return (
    <div className="card">
      <h2>実行履歴</h2>
      {runs?.length ? (
        <table><thead><tr><th>ID</th><th>指示</th><th>安全性</th><th>納品</th><th></th></tr></thead>
          <tbody>{runs.map((r) => (
            <tr key={r.id}><td>{r.id}</td><td>{r.instruction}</td>
              <td className={r.safe ? "safe" : "unsafe"}>{r.safe ? "SAFE" : "UNSAFE"}</td>
              <td>{r.delivered.join("、") || "-"}</td>
              <td><button onClick={() => onOpenReport(r.id)}>レポート</button></td></tr>))}
          </tbody></table>
      ) : <p>履歴がありません。</p>}
    </div>
  );
}
