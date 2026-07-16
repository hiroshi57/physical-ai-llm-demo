const BASE = import.meta.env?.VITE_API || "http://localhost:8000";
const h = (t) => ({ "Content-Type": "application/json", "X-Tenant-Id": t });

export async function run(t, instruction) {
  return (await fetch(`${BASE}/v1/run`, { method: "POST", headers: h(t), body: JSON.stringify({ instruction }) })).json();
}
export async function history(t) {
  return (await fetch(`${BASE}/v1/history`, { headers: h(t) })).json();
}
export function reportUrl(runId) { return `${BASE}/v1/report/${runId}`; }
