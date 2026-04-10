import { useEffect, useMemo, useState } from "react";

type RepoState = Record<string, { status: string; updated: number }>;
type ActionEvent = { repo: string; status: string; updated?: number };

const statusColor = (status: string): string => {
  switch (status) {
    case "success":
    case "healthy":
      return "#16a34a";
    case "running":
    case "degraded":
      return "#f59e0b";
    case "failed":
    case "down":
      return "#dc2626";
    default:
      return "#6b7280";
  }
};

export default function Home() {
  const [repos, setRepos] = useState<RepoState>({});
  const [actions, setActions] = useState<ActionEvent[]>([]);

  useEffect(() => {
    fetch("/api/status")
      .then((res) => res.json())
      .then((data) => {
        setRepos(data.repos || {});
        setActions(data.actions || []);
      })
      .catch(() => undefined);

    const wsUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws").trim();
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRepos((prev) => ({
        ...prev,
        [data.repo]: {
          status: data.status,
          updated: data.updated || Date.now() / 1000,
        },
      }));
      setActions((prev) => [data, ...prev].slice(0, 50));
    };

    return () => ws.close();
  }, []);

  const repoEntries = useMemo(() => Object.entries(repos).sort(([a], [b]) => a.localeCompare(b)), [repos]);

  return (
    <main style={{ fontFamily: "Inter, sans-serif", margin: "2rem auto", maxWidth: 900 }}>
      <h1>Matrix Codex Status</h1>
      <p>Live monitoring for Agent-Matrix repositories.</p>

      <h2>Repositories</h2>
      {repoEntries.map(([name, info]) => (
        <div key={name} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: "9999px", background: statusColor(info.status) }} />
          <strong>{name}</strong>
          <span>{info.status}</span>
        </div>
      ))}

      <h2 style={{ marginTop: 24 }}>Live Actions</h2>
      {actions.map((event, idx) => (
        <div key={`${event.repo}-${idx}`}>[{event.status}] {event.repo}</div>
      ))}
    </main>
  );
}
