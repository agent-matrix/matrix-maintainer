// =============================================================================
// REFERENCE ONLY — Matrix-Maintainer Admin premium UI starting point.
//
// Provided by the product owner as the visual reference for the
// matrix-maintainer admin console (the "admin.matrixhub.io" look).
//
// Adaptation notes for the real build (do NOT ship this verbatim):
//   - Replace the mock data (catalogItems/remotes/gateways) with real
//     matrix-maintainer API data: fleet health, repositories (config/repos.yml),
//     maintenance runs (matrix-codex scan-health|plan|run|report), connections
//     (config/services.yml: OllaBridge / SelfRepair / GitPilot / MatrixLab).
//   - Nav sections become: Overview, Repositories, Maintenance Runs,
//     Connections, Health, Settings.
//   - MOVE the user/account control to the TOP-RIGHT of the topbar as a
//     dropdown menu (ChatGPT/Claude style): avatar button -> menu with
//     "Settings" and "About", plus "Log out". (Currently logout is a bare
//     icon in Topbar — replace with an AccountMenu dropdown anchored right.)
//   - Keep the Matrix-rain background, glassmorphism, emerald palette.
//   - Stack: Next.js 14 + Tailwind, deployed as a Docker HF Space (port 7860)
//     behind an admin login, talking to the matrix-maintainer FastAPI backend.
// =============================================================================

import React, { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Box,
  Brain,
  CheckCircle2,
  ChevronRight,
  Code2,
  Command,
  Database,
  Download,
  Eye,
  EyeOff,
  Globe2,
  KeyRound,
  Lock,
  LogOut,
  Menu,
  Network,
  Plus,
  Rabbit,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldCheck,
  Sparkles,
  Terminal,
  Trash2,
  X,
  Zap,
} from "lucide-react";

const navItems = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "catalog", label: "Catalog", icon: Search },
  { id: "remotes", label: "Remotes", icon: Globe2 },
  { id: "gateway", label: "Gateway", icon: Network },
  { id: "entities", label: "Entities", icon: Database },
  { id: "health", label: "Health", icon: ShieldCheck },
  { id: "settings", label: "Settings", icon: Settings },
];

const catalogItems = [
  {
    id: "ent_1",
    name: "stripe-payment-agent",
    type: "AGENT",
    version: "1.2.0",
    capability: "Payments",
    downloads: "1.2K",
    status: "VERIFIED",
    summary: "Automates checkout, invoicing, refunds, and payment status workflows.",
  },
  {
    id: "ent_2",
    name: "postgres-mcp-server",
    type: "SERVER",
    version: "2.1.0",
    capability: "Database",
    downloads: "5.4K",
    status: "VERIFIED",
    summary: "Secure SQL query execution, schema inspection, and database memory layer.",
  },
  {
    id: "ent_3",
    name: "slack-notifier",
    type: "TOOL",
    version: "0.9.5",
    capability: "Communication",
    downloads: "890",
    status: "SYNCED",
    summary: "Send operational updates, alerts, and agent summaries into Slack channels.",
  },
  {
    id: "ent_4",
    name: "github-pr-manager",
    type: "AGENT",
    version: "1.0.0",
    capability: "DevOps",
    downloads: "2.1K",
    status: "VERIFIED",
    summary: "Reviews pull requests, classifies risk, and routes code-review automation.",
  },
  {
    id: "ent_5",
    name: "linear-issue-tracker",
    type: "SERVER",
    version: "1.1.2",
    capability: "Productivity",
    downloads: "1.5K",
    status: "REVIEW",
    summary: "Reads and updates tickets, labels, owners, sprint states, and roadmap signals.",
  },
];

const remotes = [
  { id: "rem_1", name: "Matrix Core Index", url: "https://index.matrix.ai/v1/catalog", status: "SYNCED", last: "2m ago", items: 142 },
  { id: "rem_2", name: "Community MCP Registry", url: "https://community.mcp.io/registry", status: "SYNCING", last: "1h ago", items: 850 },
  { id: "rem_3", name: "Local Dev Catalog", url: "http://localhost:8080/local-dev", status: "ERROR", last: "2d ago", items: 0 },
];

const gateways = [
  { id: "gw_1", name: "primary-mcp-router", transport: "SSE", url: "http://localhost:3000/sse", status: "ACTIVE", traffic: "2.4K req/h" },
  { id: "gw_2", name: "local-stdio-bridge", transport: "STDIO", url: "local process", status: "ACTIVE", traffic: "820 req/h" },
  { id: "gw_3", name: "remote-inference-node", transport: "HTTP", url: "https://api.matrix.ai/llm", status: "INACTIVE", traffic: "0 req/h" },
];

const commandHints = [
  "/sync all",
  "/search postgres",
  "/gateway status",
  "/audit entity ent_2",
  "/rotate tokens",
];

const matrixLines = Array.from({ length: 36 }, (_, i) => ({
  id: i,
  left: `${(i * 17) % 100}%`,
  delay: (i % 9) * 0.2,
  duration: 10 + (i % 7),
  text: Array.from({ length: 26 }, (_, j) => ((i + j) % 3 === 0 ? "1" : (i + j) % 5 === 0 ? "0" : "ﾏ")).join(""),
}));

function MatrixBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden bg-[#020403]">
      {matrixLines.map((line) => (
        <motion.div
          key={line.id}
          className="absolute top-[-45%] font-mono text-[10px] leading-3 text-emerald-400/35"
          style={{ left: line.left, writingMode: "vertical-rl" }}
          animate={{ y: ["-15vh", "145vh"] }}
          transition={{ duration: line.duration, repeat: Infinity, delay: line.delay, ease: "linear" }}
        >
          {line.text}
        </motion.div>
      ))}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(0,255,136,0.14),transparent_36%),radial-gradient(circle_at_90%_10%,rgba(16,185,129,0.08),transparent_30%),linear-gradient(180deg,rgba(2,4,3,0.55),#020403_88%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,255,136,0.045)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,136,0.045)_1px,transparent_1px)] bg-[size:42px_42px] opacity-40" />
    </div>
  );
}

function Badge({ children, tone = "emerald" }) {
  const map = {
    emerald: "border-emerald-300/20 bg-emerald-400/10 text-emerald-200",
    amber: "border-amber-300/20 bg-amber-400/10 text-amber-200",
    rose: "border-rose-300/20 bg-rose-400/10 text-rose-200",
    zinc: "border-zinc-300/10 bg-zinc-400/10 text-zinc-300",
    cyan: "border-cyan-300/20 bg-cyan-400/10 text-cyan-200",
  };
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${map[tone] || map.emerald}`}>{children}</span>;
}

function statusTone(status) {
  const value = String(status).toUpperCase();
  if (["ACTIVE", "SYNCED", "VERIFIED", "HEALTHY", "OK"].includes(value)) return "emerald";
  if (["SYNCING", "REVIEW"].includes(value)) return "amber";
  if (["ERROR", "INACTIVE", "UNHEALTHY"].includes(value)) return "rose";
  return "zinc";
}

function scoreItem(item, query) {
  const q = query.trim().toLowerCase();
  const haystack = `${item.name} ${item.type} ${item.capability} ${item.summary}`.toLowerCase();
  if (!q) return 90 + (item.status === "VERIFIED" ? 8 : 0);
  return q.split(" ").filter(Boolean).reduce((score, token) => {
    if (item.name.toLowerCase().includes(token)) return score + 36;
    if (item.capability.toLowerCase().includes(token)) return score + 24;
    if (item.type.toLowerCase().includes(token)) return score + 18;
    if (haystack.includes(token)) return score + 10;
    return score;
  }, item.status === "VERIFIED" ? 8 : 0);
}

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState("");

  function submit(event) {
    event.preventDefault();
    if (username === "admin" && password === "admin") {
      setError("");
      onLogin();
    } else {
      setError("Invalid admin credentials. Use admin / admin for this reference build.");
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020403] text-emerald-50">
      <MatrixBackground />
      <div className="relative z-10 grid min-h-screen place-items-center px-4">
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-3xl border border-emerald-300/25 bg-emerald-400/10 shadow-[0_0_50px_rgba(0,255,136,0.18)]">
              <ShieldCheck className="h-8 w-8 text-emerald-300" />
            </div>
            <p className="font-mono text-xs uppercase tracking-[0.35em] text-emerald-300/70">MatrixHub Admin</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-[-0.06em] text-emerald-50">Operator access</h1>
            <p className="mt-3 text-sm leading-6 text-emerald-50/58">Secure console for catalog, gateway, remotes, entities, and system health.</p>
          </div>

          <form onSubmit={submit} className="rounded-[2rem] border border-emerald-300/18 bg-[#06100B]/82 p-6 shadow-[0_0_80px_rgba(0,255,136,0.12)] backdrop-blur-xl">
            {error && <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 p-3 text-sm text-rose-200">{error}</div>}
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300/60">Username</label>
            <div className="mb-4 flex items-center gap-3 rounded-2xl border border-emerald-400/12 bg-black/55 px-4">
              <Terminal className="h-4 w-4 text-emerald-300" />
              <input value={username} onChange={(e) => setUsername(e.target.value)} className="h-12 w-full bg-transparent text-emerald-50 outline-none placeholder:text-emerald-300/35" placeholder="admin" />
            </div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300/60">Password</label>
            <div className="mb-5 flex items-center gap-3 rounded-2xl border border-emerald-400/12 bg-black/55 px-4">
              <Lock className="h-4 w-4 text-emerald-300" />
              <input type={visible ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} className="h-12 w-full bg-transparent text-emerald-50 outline-none placeholder:text-emerald-300/35" placeholder="admin" />
              <button type="button" onClick={() => setVisible(!visible)} className="text-emerald-200/70 hover:text-emerald-200">{visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button>
            </div>
            <button className="h-12 w-full rounded-2xl bg-emerald-400 font-semibold text-black shadow-[0_0_32px_rgba(0,255,136,0.18)] hover:bg-emerald-300">Enter admin console</button>
            <p className="mt-4 text-center font-mono text-[11px] text-emerald-300/45">reference credentials: admin / admin</p>
          </form>
        </motion.div>
      </div>
    </main>
  );
}

function Sidebar({ active, setActive, open, setOpen }) {
  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-50 hidden w-72 border-r border-emerald-300/10 bg-black/55 p-4 backdrop-blur-xl lg:block">
        <Brand />
        <nav className="mt-8 space-y-1">
          {navItems.map((item) => <NavButton key={item.id} item={item} active={active} setActive={setActive} />)}
        </nav>
        <div className="absolute bottom-4 left-4 right-4 rounded-3xl border border-emerald-300/12 bg-emerald-400/5 p-4">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl border border-emerald-300/20 bg-black text-emerald-300">
            <Rabbit className="h-5 w-5" />
          </div>
          <p className="text-sm font-semibold text-emerald-50">Alive Admin Layer</p>
          <p className="mt-1 text-xs leading-5 text-emerald-50/50">Use command mode for sync, audit, gateway checks, and secure operations.</p>
        </div>
      </aside>

      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-[70] bg-black/70 backdrop-blur-sm lg:hidden">
            <motion.aside initial={{ x: -320 }} animate={{ x: 0 }} exit={{ x: -320 }} className="h-full w-80 border-r border-emerald-300/10 bg-[#020403] p-4">
              <div className="flex items-center justify-between">
                <Brand />
                <button onClick={() => setOpen(false)} className="rounded-xl border border-emerald-400/15 p-2 text-emerald-100"><X className="h-5 w-5" /></button>
              </div>
              <nav className="mt-8 space-y-1">
                {navItems.map((item) => <NavButton key={item.id} item={item} active={active} setActive={(id) => { setActive(id); setOpen(false); }} />)}
              </nav>
            </motion.aside>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-emerald-400/30 bg-emerald-400/10 shadow-[0_0_30px_rgba(0,255,136,0.16)]">
        <Box className="h-5 w-5 text-emerald-300" />
      </div>
      <div>
        <p className="text-lg font-semibold tracking-tight text-emerald-50">MatrixHub</p>
        <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-300/55">admin console</p>
      </div>
    </div>
  );
}

function NavButton({ item, active, setActive }) {
  const Icon = item.icon;
  const selected = active === item.id;
  return (
    <button onClick={() => setActive(item.id)} className={`flex w-full items-center justify-between rounded-2xl px-4 py-3 text-sm transition ${selected ? "border border-emerald-300/20 bg-emerald-400/12 text-emerald-100 shadow-[0_0_22px_rgba(0,255,136,0.08)]" : "text-emerald-50/58 hover:bg-emerald-400/6 hover:text-emerald-100"}`}>
      <span className="flex items-center gap-3"><Icon className="h-4 w-4" /> {item.label}</span>
      {selected && <ChevronRight className="h-4 w-4 text-emerald-300" />}
    </button>
  );
}

// NOTE for real build: replace the bare logout button below with an
// AccountMenu dropdown anchored to the top-right (avatar -> Settings / About / Log out).
function Topbar({ active, setOpen, onLogout, onCommand }) {
  const label = navItems.find((item) => item.id === active)?.label || "Overview";
  return (
    <header className="sticky top-0 z-40 border-b border-emerald-300/10 bg-black/45 backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between px-4 lg:px-8">
        <div className="flex items-center gap-3">
          <button onClick={() => setOpen(true)} className="rounded-xl border border-emerald-400/15 p-2 text-emerald-100 lg:hidden"><Menu className="h-5 w-5" /></button>
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-emerald-300/55">Current module</p>
            <h1 className="text-xl font-semibold tracking-tight text-emerald-50">{label}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onCommand} className="hidden rounded-2xl border border-emerald-300/15 bg-emerald-400/5 px-4 py-2 text-sm text-emerald-100 hover:bg-emerald-400/10 md:inline-flex"><Command className="mr-2 h-4 w-4" /> Command</button>
          <div className="hidden rounded-2xl border border-emerald-300/12 bg-black/40 px-3 py-2 text-xs text-emerald-50/60 sm:block">admin@matrixhub.io</div>
          <button onClick={onLogout} className="rounded-2xl border border-emerald-300/15 bg-black/30 p-2 text-emerald-100 hover:bg-rose-400/10 hover:text-rose-200"><LogOut className="h-4 w-4" /></button>
        </div>
      </div>
    </header>
  );
}

function MetricCard({ icon: Icon, label, value, sub, tone = "emerald" }) {
  const toneClass = tone === "rose" ? "text-rose-300 bg-rose-400/10 border-rose-300/20" : tone === "amber" ? "text-amber-300 bg-amber-400/10 border-amber-300/20" : "text-emerald-300 bg-emerald-400/10 border-emerald-300/20";
  return (
    <div className="rounded-[1.5rem] border border-emerald-300/12 bg-[#07110C]/70 p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <div className="flex items-start justify-between">
        <div className={`flex h-11 w-11 items-center justify-center rounded-2xl border ${toneClass}`}><Icon className="h-5 w-5" /></div>
        <span className="font-mono text-[11px] text-emerald-300/45">LIVE</span>
      </div>
      <p className="mt-5 text-sm text-emerald-50/55">{label}</p>
      <p className="mt-1 text-3xl font-semibold tracking-tight text-emerald-50">{value}</p>
      <p className="mt-2 text-xs text-emerald-50/42">{sub}</p>
    </div>
  );
}

function Overview({ setActive, openCommand }) {
  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-emerald-300/14 bg-[#06100B]/76 p-6 shadow-[0_0_80px_rgba(0,255,136,0.08)] backdrop-blur lg:p-8">
        <MatrixBackground />
        <div className="relative z-10 grid gap-8 lg:grid-cols-[1fr_360px] lg:items-center">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-400/10 px-4 py-2 font-mono text-xs uppercase tracking-[0.18em] text-emerald-200"><Activity className="h-4 w-4" /> Admin system online</div>
            <h2 className="max-w-3xl text-4xl font-semibold tracking-[-0.06em] text-emerald-50 lg:text-6xl">Control the MatrixHub ecosystem.</h2>
            <p className="mt-5 max-w-2xl text-base leading-7 text-emerald-50/62">Manage federated catalogs, MCP gateways, entities, health, and secure settings from a premium operator console inspired by the previous MatrixHub interface.</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <button onClick={() => setActive("catalog")} className="rounded-2xl bg-emerald-400 px-5 py-3 font-semibold text-black hover:bg-emerald-300"><Search className="mr-2 inline h-4 w-4" /> Open catalog</button>
              <button onClick={openCommand} className="rounded-2xl border border-emerald-300/20 bg-black/35 px-5 py-3 font-semibold text-emerald-100 hover:bg-emerald-400/10"><Terminal className="mr-2 inline h-4 w-4" /> Alive command</button>
            </div>
          </div>
          <div className="rounded-[1.5rem] border border-emerald-300/14 bg-black/50 p-5 font-mono text-xs text-emerald-100/80">
            <p className="mb-4 text-emerald-300">matrix-admin&gt; health --summary</p>
            <p>hub_api: operational</p>
            <p>gateway: active</p>
            <p>remotes: 2 synced · 1 degraded</p>
            <p>entities: 5 indexed</p>
            <p className="mt-4 text-emerald-300">deployment_confidence: 94%</p>
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={Database} label="Indexed entities" value="2,481" sub="+142 from last sync" />
        <MetricCard icon={Network} label="Gateway traffic" value="3.2K" sub="requests this hour" />
        <MetricCard icon={Globe2} label="Remote indexes" value="3" sub="2 healthy · 1 degraded" tone="amber" />
        <MetricCard icon={ShieldCheck} label="System health" value="99.98%" sub="rolling 24h availability" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <HealthPanel />
        <ActivityFeed />
      </div>
    </div>
  );
}

function CatalogView() {
  const [query, setQuery] = useState("");
  const ranked = useMemo(() => catalogItems.map((item) => ({ ...item, score: scoreItem(item, query) })).filter((item) => !query || item.score > 0).sort((a, b) => b.score - a.score || a.name.localeCompare(b.name)), [query]);
  return (
    <div className="space-y-6">
      <div className="rounded-[2rem] border border-emerald-300/14 bg-[#06100B]/76 p-6 backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-emerald-300/65">Deterministic meta-search</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-emerald-50">Catalog control</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-emerald-50/55">Search, rank, verify, inspect, and install MCP agents, servers, and tools.</p>
          </div>
          <button className="h-12 rounded-2xl bg-emerald-400 px-5 font-semibold text-black hover:bg-emerald-300"><Plus className="mr-2 inline h-4 w-4" /> Add entity</button>
        </div>
        <div className="mt-6 flex items-center gap-3 rounded-2xl border border-emerald-300/14 bg-black/45 px-4">
          <Search className="h-5 w-5 text-emerald-300" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search agents, servers, capabilities..." className="h-14 flex-1 bg-transparent text-emerald-50 outline-none placeholder:text-emerald-300/35" />
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {["All", "AGENT", "SERVER", "TOOL", "Payments", "Database", "DevOps"].map((tag) => <button key={tag} onClick={() => setQuery(tag === "All" ? "" : tag)} className="rounded-full border border-emerald-400/15 bg-emerald-400/5 px-3 py-2 text-xs text-emerald-100/75 hover:bg-emerald-400/10">{tag}</button>)}
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {ranked.map((item) => <CatalogCard key={item.id} item={item} />)}
      </div>
    </div>
  );
}

function CatalogCard({ item }) {
  return (
    <div className="rounded-[1.5rem] border border-emerald-300/12 bg-[#07110C]/70 p-5 shadow-xl shadow-black/20 backdrop-blur transition hover:-translate-y-1 hover:border-emerald-300/35 hover:shadow-[0_0_50px_rgba(0,255,136,0.1)]">
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-400/20 bg-black/45 font-mono text-sm text-emerald-300">{item.type.slice(0, 2)}</div>
        <Badge tone={statusTone(item.status)}>{item.status}</Badge>
      </div>
      <p className="mt-5 font-mono text-xs uppercase tracking-[0.22em] text-emerald-300/55">{item.type} · v{item.version}</p>
      <h3 className="mt-2 text-xl font-semibold text-emerald-50">{item.name}</h3>
      <p className="mt-3 text-sm leading-6 text-emerald-50/58">{item.summary}</p>
      <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-emerald-400/10 pt-4 text-xs text-emerald-50/55">
        <span>{item.capability}</span>
        <span>{item.downloads} downloads</span>
        <span className="ml-auto font-mono text-emerald-300/70">score {Math.round(item.score)}</span>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <button className="rounded-2xl bg-emerald-400 px-4 py-2.5 font-semibold text-black hover:bg-emerald-300">Install</button>
        <button className="rounded-2xl border border-emerald-300/15 bg-transparent px-4 py-2.5 text-emerald-100 hover:bg-emerald-400/10">Inspect</button>
      </div>
    </div>
  );
}

function RemotesView() {
  return <TableView title="Index remotes" subtitle="Manage upstream catalogs and synchronization schedules." action="Sync all" icon={RefreshCw} rows={remotes} kind="remotes" />;
}

function GatewayView() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard icon={Network} label="Active bridges" value="2" sub="SSE + STDIO online" />
        <MetricCard icon={Zap} label="Traffic" value="3.2K" sub="requests this hour" />
        <MetricCard icon={Server} label="Inactive nodes" value="1" sub="remote inference paused" tone="amber" />
      </div>
      <TableView title="Gateway control" subtitle="Active MCP server bridges and connection pools." action="Register server" icon={Plus} rows={gateways} kind="gateway" />
    </div>
  );
}

function EntitiesView() {
  return <TableView title="Entity database" subtitle="Raw view of ingested MCP entities with versions and capabilities." action="Export CSV" icon={Download} rows={catalogItems} kind="entities" />;
}

function TableView({ title, subtitle, action, icon: Icon, rows, kind }) {
  return (
    <div className="rounded-[2rem] border border-emerald-300/14 bg-[#06100B]/72 p-5 shadow-xl shadow-black/20 backdrop-blur lg:p-6">
      <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-emerald-50">{title}</h2>
          <p className="mt-1 text-sm text-emerald-50/52">{subtitle}</p>
        </div>
        <button className="h-11 rounded-2xl bg-emerald-400 px-5 font-semibold text-black hover:bg-emerald-300"><Icon className="mr-2 inline h-4 w-4" /> {action}</button>
      </div>
      <div className="overflow-hidden rounded-2xl border border-emerald-300/10">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-emerald-400/[0.04] text-xs uppercase tracking-[0.16em] text-emerald-300/55">
              <tr>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type / URL</th>
                <th className="px-4 py-3">Metric</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-emerald-300/8">
              {rows.map((row) => (
                <tr key={row.id} className="bg-black/20 text-emerald-50/72 transition hover:bg-emerald-400/[0.035]">
                  <td className="px-4 py-4"><Badge tone={statusTone(row.status)}>{row.status || row.type}</Badge></td>
                  <td className="px-4 py-4 font-medium text-emerald-50">{row.name}</td>
                  <td className="px-4 py-4 font-mono text-xs text-emerald-50/48">{row.url || `${row.type} · ${row.version}`}</td>
                  <td className="px-4 py-4 text-emerald-50/58">{row.items ?? row.traffic ?? row.downloads ?? row.capability}</td>
                  <td className="px-4 py-4 text-right">
                    <div className="inline-flex gap-2">
                      <button className="rounded-xl border border-emerald-300/12 p-2 text-emerald-200 hover:bg-emerald-400/10"><Eye className="h-4 w-4" /></button>
                      {kind === "remotes" && <button className="rounded-xl border border-rose-300/12 p-2 text-rose-200 hover:bg-rose-400/10"><Trash2 className="h-4 w-4" /></button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function HealthPanel() {
  const bars = [34, 52, 26, 64, 46, 38, 58, 44, 70, 62, 36, 28, 48, 42];
  return (
    <div className="rounded-[2rem] border border-emerald-300/14 bg-[#06100B]/72 p-6 shadow-xl shadow-black/20 backdrop-blur">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-emerald-50">System health</h2>
          <p className="mt-1 text-sm text-emerald-50/52">Hub API, gateway, indexer, and storage checks.</p>
        </div>
        <Badge>HEALTHY</Badge>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {["Hub API", "Gateway", "Indexer"].map((item) => <div key={item} className="rounded-2xl border border-emerald-300/10 bg-black/30 p-4"><CheckCircle2 className="mb-3 h-5 w-5 text-emerald-300" /><p className="font-semibold text-emerald-50">{item}</p><p className="mt-1 text-xs text-emerald-50/45">Operational</p></div>)}
      </div>
      <div className="mt-6 rounded-2xl border border-emerald-300/10 bg-black/30 p-4">
        <div className="mb-3 flex justify-between text-xs text-emerald-50/45"><span>Error rate 24h</span><span>0.02% avg</span></div>
        <div className="flex h-24 items-end gap-2">
          {bars.map((h, i) => <div key={i} className="flex-1 rounded-t bg-emerald-400/20 transition hover:bg-emerald-400/45" style={{ height: `${h}%` }} />)}
        </div>
      </div>
    </div>
  );
}

function ActivityFeed() {
  const events = [
    ["sync", "Community MCP Registry sync started", "1m ago", "amber"],
    ["verify", "postgres-mcp-server passed policy check", "8m ago", "emerald"],
    ["gateway", "local-stdio-bridge traffic spike detected", "14m ago", "cyan"],
    ["error", "Local Dev Catalog returned 503", "2d ago", "rose"],
  ];
  return (
    <div className="rounded-[2rem] border border-emerald-300/14 bg-[#06100B]/72 p-6 shadow-xl shadow-black/20 backdrop-blur">
      <h2 className="text-2xl font-semibold tracking-tight text-emerald-50">Audit activity</h2>
      <p className="mt-1 text-sm text-emerald-50/52">Recent operator and system events.</p>
      <div className="mt-6 space-y-3">
        {events.map(([type, text, time, tone]) => <div key={text} className="flex items-start gap-3 rounded-2xl border border-emerald-300/8 bg-black/25 p-3"><Badge tone={tone}>{type}</Badge><div className="min-w-0 flex-1"><p className="text-sm text-emerald-50/78">{text}</p><p className="mt-1 text-xs text-emerald-50/40">{time}</p></div></div>)}
      </div>
    </div>
  );
}

function HealthView() {
  return <div className="space-y-6"><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"><MetricCard icon={ShieldCheck} label="Status" value="Healthy" sub="all critical checks pass" /><MetricCard icon={Activity} label="Uptime" value="99.98%" sub="rolling 30 days" /><MetricCard icon={AlertTriangle} label="Error rate" value="0.02%" sub="last 24h" /><MetricCard icon={Zap} label="Throughput" value="3.2K" sub="requests per hour" /></div><HealthPanel /></div>;
}

function SettingsView() {
  const [adminToken, setAdminToken] = useState(false);
  const [gatewaySecret, setGatewaySecret] = useState(false);
  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="rounded-[2rem] border border-emerald-300/14 bg-[#06100B]/72 p-6 backdrop-blur">
        <h2 className="text-2xl font-semibold tracking-tight text-emerald-50">Authentication tokens</h2>
        <p className="mt-1 text-sm text-emerald-50/52">Reveal only during secure operator sessions.</p>
        <div className="mt-6 space-y-4">
          <TokenRow label="Admin API Token" value="sk-matrix-admin-xxxxxxxxxxxx" visible={adminToken} setVisible={setAdminToken} />
          <TokenRow label="Gateway Secret" value="gw-matrix-router-xxxxxxxxxxx" visible={gatewaySecret} setVisible={setGatewaySecret} />
        </div>
      </div>
      <div className="rounded-[2rem] border border-emerald-300/14 bg-[#06100B]/72 p-6 backdrop-blur">
        <h2 className="text-2xl font-semibold tracking-tight text-emerald-50">Environment</h2>
        <div className="mt-6 space-y-3 font-mono text-xs">
          {[['HUB_PUBLIC_URL','https://hub.matrix.ai'], ['GATEWAY_MODE','HYBRID'], ['DB_CONNECTION','CONNECTED'], ['AUTH_MODE','LOCAL_ADMIN']].map(([k,v]) => <div key={k} className="flex justify-between gap-4 border-b border-emerald-300/8 pb-3"><span className="text-emerald-50/45">{k}</span><span className="text-emerald-200">{v}</span></div>)}
        </div>
      </div>
    </div>
  );
}

function TokenRow({ label, value, visible, setVisible }) {
  return (
    <div>
      <label className="mb-2 block text-xs uppercase tracking-[0.2em] text-emerald-300/55">{label}</label>
      <div className="flex gap-2 rounded-2xl border border-emerald-300/10 bg-black/35 p-2">
        <div className="flex flex-1 items-center gap-2 px-2"><KeyRound className="h-4 w-4 text-emerald-300" /><input readOnly value={visible ? value : "••••••••••••••••••••••••"} className="h-10 flex-1 bg-transparent font-mono text-sm text-emerald-50/62 outline-none" /></div>
        <button onClick={() => setVisible(!visible)} className="rounded-xl border border-emerald-300/14 px-3 text-sm text-emerald-100 hover:bg-emerald-400/10">{visible ? "Hide" : "Reveal"}</button>
      </div>
    </div>
  );
}

function CommandOverlay({ open, onClose, setActive }) {
  const [value, setValue] = useState("");
  const [lines, setLines] = useState(["matrix-admin console ready", "type /help, /sync all, /gateway status, /audit entity ent_2"]);
  function run(cmd) {
    const clean = cmd.trim();
    if (!clean) return;
    if (clean === "/clear") { setLines(["terminal cleared"]); setValue(""); return; }
    const lower = clean.toLowerCase();
    const response = lower.includes("sync") ? ["sync requested", "rem_1: synced", "rem_2: syncing", "rem_3: error retained"] : lower.includes("gateway") ? ["gateway status", "primary-mcp-router: active", "local-stdio-bridge: active", "remote-inference-node: inactive"] : lower.includes("audit") ? ["audit report", "entity: ent_2", "policy: passed", "risk: low", "install: approved"] : lower.includes("search") ? ["search routed to catalog module", "deterministic meta-engine online"] : lower === "/help" ? ["commands", "/sync all", "/gateway status", "/audit entity <id>", "/search <query>", "/clear"] : ["alive response", "command accepted", "route: operator review"];
    setLines((current) => [...current, `matrix-admin> ${clean}`, ...response]);
    setValue("");
    if (lower.includes("search")) setActive("catalog");
  }
  return (
    <AnimatePresence>
      {open && <div className="fixed inset-0 z-[90] grid place-items-end bg-black/75 p-3 backdrop-blur-md sm:place-items-center sm:p-6"><motion.div initial={{ opacity: 0, y: 24, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 18, scale: 0.98 }} className="relative flex h-[78svh] w-full max-w-4xl flex-col overflow-hidden rounded-[1.5rem] border border-emerald-300/25 bg-[#020403] shadow-[0_0_120px_rgba(0,255,136,0.22)]"><MatrixBackground /><div className="relative flex h-14 items-center justify-between border-b border-emerald-300/12 bg-emerald-400/5 px-4"><div className="flex items-center gap-3"><Terminal className="h-5 w-5 text-emerald-300" /><div><p className="font-mono text-sm uppercase tracking-[0.18em] text-emerald-100">Alive admin command</p><p className="text-xs text-emerald-300/50">secure operator launcher</p></div></div><button onClick={onClose} className="rounded-xl border border-emerald-300/12 p-2 text-emerald-100"><X className="h-4 w-4" /></button></div><div className="relative flex-1 overflow-auto p-5 font-mono text-sm leading-7 text-emerald-100/82">{lines.map((line, i) => <p key={i} className={line.startsWith("matrix-admin>") ? "text-emerald-300" : ""}>{line}</p>)}</div><div className="relative border-t border-emerald-300/12 bg-black/55 p-4"><div className="mb-3 flex gap-2 overflow-x-auto">{commandHints.map((hint) => <button key={hint} onClick={() => run(hint)} className="shrink-0 rounded-full border border-emerald-300/12 bg-emerald-400/5 px-3 py-2 font-mono text-xs text-emerald-100/70 hover:bg-emerald-400/10">{hint}</button>)}</div><form onSubmit={(e) => { e.preventDefault(); run(value); }} className="flex items-center gap-3 rounded-2xl border border-emerald-300/20 bg-[#06100B] px-4"><span className="font-mono text-emerald-300">admin&gt;</span><input value={value} onChange={(e) => setValue(e.target.value)} className="h-12 flex-1 bg-transparent font-mono text-sm text-emerald-50 outline-none placeholder:text-emerald-300/35" placeholder="type command..." /><button className="rounded-xl bg-emerald-400 p-2 text-black"><Command className="h-4 w-4" /></button></form></div></motion.div></div>}
    </AnimatePresence>
  );
}

function Content({ active, setActive, openCommand }) {
  if (active === "overview") return <Overview setActive={setActive} openCommand={openCommand} />;
  if (active === "catalog") return <CatalogView />;
  if (active === "remotes") return <RemotesView />;
  if (active === "gateway") return <GatewayView />;
  if (active === "entities") return <EntitiesView />;
  if (active === "health") return <HealthView />;
  return <SettingsView />;
}

export default function MatrixHubAdminPremiumUI() {
  const [authenticated, setAuthenticated] = useState(false);
  const [active, setActive] = useState("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);

  if (!authenticated) return <LoginScreen onLogin={() => setAuthenticated(true)} />;

  return (
    <main className="min-h-screen overflow-hidden bg-[#020403] text-emerald-50 antialiased selection:bg-emerald-300 selection:text-black">
      <MatrixBackground />
      <Sidebar active={active} setActive={setActive} open={sidebarOpen} setOpen={setSidebarOpen} />
      <CommandOverlay open={commandOpen} onClose={() => setCommandOpen(false)} setActive={setActive} />
      <div className="relative z-10 lg:pl-72">
        <Topbar active={active} setOpen={setSidebarOpen} onLogout={() => setAuthenticated(false)} onCommand={() => setCommandOpen(true)} />
        <div className="mx-auto max-w-[1500px] px-4 py-6 lg:px-8 lg:py-8">
          <Content active={active} setActive={setActive} openCommand={() => setCommandOpen(true)} />
        </div>
      </div>
    </main>
  );
}
