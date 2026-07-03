import { useCallback, useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";

type Category = {
  id: string;
  name: string;
  enabled: boolean;
  priority: number;
  include_keywords: string[];
  exclude_keywords: string[];
  source_ids: string[];
  result_target: number;
  freshness_hours: number;
  minimum_relevance: number;
  color: string;
};
type Source = { name: string; url: string; enabled?: boolean; type?: string };
type Event = {
  event_id: string;
  run_id: string;
  trace_id: string;
  timestamp: number;
  stage: string;
  status: string;
  message?: string;
  exit_code?: number;
};
type Result = {
  title: string;
  url: string;
  source: string;
  published: string;
  topics?: string[];
  categories?: string[];
  ranking?: { top_score?: number };
  detection?: { type?: string };
};
type Config = Record<string, string | number | boolean>;
type Dashboard = {
  stats: Record<string, number>;
  run: Record<string, unknown>;
  events: Event[];
  categories: Category[];
  credential_status: string;
  credential_statuses: Record<string, string>;
};
type ModelOption = {
  id: string;
  name: string;
  provider: string;
  metadata?: Record<string, unknown>;
};
type State = {
  config: Config;
  sources: { rss: Source[]; scrape: Source[] };
  run: { status: string; log: string[]; run_id?: string; started_at?: string };
  stats: Record<string, number>;
};

const nav = [
  "Overview",
  "Live run",
  "Categories",
  "Sources",
  "Results",
  "Failures",
  "Traces",
  "Schedules",
  "Configuration",
] as const;
type View = (typeof nav)[number];
const api = async <T,>(url: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || data.errors?.join(". ") || "Request failed");
  return data;
};

function Stat({
  label,
  value,
  tone = "cyan",
}: {
  label: string;
  value: string | number;
  tone?: string;
}) {
  return (
    <div className={`stat tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
function Status({ value }: { value: string }) {
  return <span className={`status status-${value}`}>{value}</span>;
}
function Empty({ children }: { children: string }) {
  return <div className="empty">{children}</div>;
}

function Overview({ dashboard }: { dashboard: Dashboard | null }) {
  const events = dashboard?.events || [];
  const buckets = useMemo(() => {
    const map = new Map<string, { ok: number; error: number }>();
    events.forEach((event) => {
      const time = new Date(event.timestamp * 1000).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      const bucket = map.get(time) || { ok: 0, error: 0 };
      event.status === "error" ? bucket.error++ : bucket.ok++;
      map.set(time, bucket);
    });
    return [...map.entries()].slice(-18);
  }, [events]);
  const chart = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    legend: { textStyle: { color: "#7f91a7" }, data: ["events", "errors"] },
    grid: { left: 35, right: 12, top: 35, bottom: 25 },
    xAxis: {
      type: "category",
      data: buckets.map((x) => x[0]),
      axisLabel: { color: "#66788d" },
      axisLine: { lineStyle: { color: "#263749" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#66788d" },
      splitLine: { lineStyle: { color: "#162536" } },
    },
    series: [
      {
        name: "events",
        type: "line",
        smooth: true,
        showSymbol: false,
        data: buckets.map((x) => x[1].ok),
        lineStyle: { color: "#22d3ee" },
        areaStyle: { color: "rgba(34,211,238,.12)" },
      },
      {
        name: "errors",
        type: "line",
        showSymbol: false,
        data: buckets.map((x) => x[1].error),
        lineStyle: { color: "#fb7185" },
      },
    ],
  };
  return (
    <div className="view-stack">
      <div className="stats-grid">
        <Stat label="articles" value={dashboard?.stats.articles ?? 0} />
        <Stat
          label="selected"
          value={dashboard?.stats.session_articles ?? 0}
          tone="green"
        />
        <Stat
          label="sources"
          value={dashboard?.stats.sources ?? 0}
          tone="violet"
        />
        <Stat label="runs" value={dashboard?.stats.runs ?? 0} />
        <Stat label="events" value={dashboard?.stats.telemetry_events ?? 0} />
        <Stat
          label="failures"
          value={dashboard?.stats.failures ?? 0}
          tone="red"
        />
      </div>
      <section className="panel chart-panel">
        <div className="panel-title">
          <span>Pipeline activity</span>
          <small>events / minute</small>
        </div>
        {buckets.length ? (
          <ReactECharts option={chart} className="activity-chart" />
        ) : (
          <Empty>No telemetry yet. Run a scrape to populate this chart.</Empty>
        )}
      </section>
      <div className="split">
        <section className="panel">
          <div className="panel-title">
            <span>Stage volume</span>
            <small>bounded labels</small>
          </div>
          <div className="metric-list">
            {Object.entries(dashboard?.stats || {})
              .slice(0, 8)
              .map(([key, value]) => (
                <div key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <b>{value}</b>
                </div>
              ))}
          </div>
        </section>
        <section className="panel">
          <div className="panel-title">
            <span>Recent events</span>
            <small>latest 8</small>
          </div>
          <EventList events={events.slice(-8).reverse()} />
        </section>
      </div>
    </div>
  );
}
function EventList({ events }: { events: Event[] }) {
  return events.length ? (
    <div className="event-list">
      {events.map((event) => (
        <div className="event-row" key={event.event_id}>
          <Status value={event.status} />
          <span>{event.stage.replaceAll("_", " ")}</span>
          <time>{new Date(event.timestamp * 1000).toLocaleTimeString()}</time>
        </div>
      ))}
    </div>
  ) : (
    <Empty>No events recorded.</Empty>
  );
}
function LiveRun({
  state,
  onCancel,
}: {
  state: State | null;
  onCancel: () => void;
}) {
  const run = state?.run;
  return (
    <div className="view-stack">
      <div className="stats-grid">
        <Stat
          label="state"
          value={run?.status || "idle"}
          tone={run?.status === "failed" ? "red" : "green"}
        />
        <Stat label="run id" value={run?.run_id?.slice(0, 8) || "—"} />
        <Stat label="log lines" value={run?.log?.length || 0} />
      </div>
      <section className="panel">
        <div className="panel-title">
          <span>Execution stream</span>
          <button
            className="button danger"
            disabled={run?.status !== "running"}
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
        <pre className="console">
          {run?.log?.join("\n") || "No active execution."}
        </pre>
      </section>
    </div>
  );
}

function Categories({
  items,
  onSave,
}: {
  items: Category[];
  onSave: (items: Category[]) => void;
}) {
  const [rows, setRows] = useState(items);
  const [selected, setSelected] = useState<Category | null>(null);
  useEffect(() => setRows(items), [items]);
  const update = (next: Category) => {
    setRows((current) =>
      current.map((item) => (item.id === next.id ? next : item)),
    );
    setSelected(next);
  };
  return (
    <div className="with-inspector">
      <section className="panel table-panel">
        <div className="panel-title">
          <span>{rows.length} categories</span>
          <button className="button primary" onClick={() => onSave(rows)}>
            Save
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>On</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Target</th>
              <th>Freshness</th>
              <th>Threshold</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} onClick={() => setSelected(row)}>
                <td>
                  <input
                    type="checkbox"
                    checked={row.enabled}
                    onChange={(event) =>
                      update({ ...row, enabled: event.target.checked })
                    }
                  />
                </td>
                <td>
                  <code>{row.color}</code> {row.name}
                </td>
                <td>{row.priority}</td>
                <td>{row.result_target}</td>
                <td>{row.freshness_hours}h</td>
                <td>{Math.round(row.minimum_relevance * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {selected && (
        <aside className="inspector">
          <div className="panel-title">
            <span>Edit category</span>
            <button className="icon-button" onClick={() => setSelected(null)}>
              ×
            </button>
          </div>
          <Field
            label="Name"
            value={selected.name}
            onChange={(value) => update({ ...selected, name: value })}
          />
          <Field
            label="Priority"
            type="number"
            value={selected.priority}
            onChange={(value) =>
              update({ ...selected, priority: Number(value) })
            }
          />
          <Field
            label="Result target"
            type="number"
            value={selected.result_target}
            onChange={(value) =>
              update({ ...selected, result_target: Number(value) })
            }
          />
          <Field
            label="Freshness hours"
            type="number"
            value={selected.freshness_hours}
            onChange={(value) =>
              update({ ...selected, freshness_hours: Number(value) })
            }
          />
          <Field
            label="Include keywords"
            value={selected.include_keywords.join(", ")}
            onChange={(value) =>
              update({
                ...selected,
                include_keywords: value
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean),
              })
            }
          />
          <Field
            label="Exclude keywords"
            value={selected.exclude_keywords.join(", ")}
            onChange={(value) =>
              update({
                ...selected,
                exclude_keywords: value
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean),
              })
            }
          />
          <Field
            label="Chart color"
            type="color"
            value={selected.color}
            onChange={(value) => update({ ...selected, color: value })}
          />
        </aside>
      )}
    </div>
  );
}
function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
function Sources({
  sources,
  onSave,
  onTest,
}: {
  sources: { rss: Source[]; scrape: Source[] };
  onSave: (value: { rss: Source[]; scrape: Source[] }) => void;
  onTest: (source: Source) => void;
}) {
  const [value, setValue] = useState(sources);
  useEffect(() => setValue(sources), [sources]);
  const all = [
    ...value.rss.map((x) => ({ ...x, group: "rss" })),
    ...value.scrape.map((x) => ({ ...x, group: "scrape" })),
  ];
  return (
    <section className="panel table-panel">
      <div className="panel-title">
        <span>{all.length} sources</span>
        <button className="button primary" onClick={() => onSave(value)}>
          Save
        </button>
      </div>
      <table>
        <thead>
          <tr>
            <th>On</th>
            <th>Source</th>
            <th>Type</th>
            <th>URL</th>
            <th>Probe</th>
          </tr>
        </thead>
        <tbody>
          {all.map((source, index) => (
            <tr key={`${source.group}-${source.url}`}>
              <td>
                <input
                  type="checkbox"
                  checked={source.enabled !== false}
                  onChange={(event) => {
                    const key = source.group as "rss" | "scrape";
                    setValue((current) => ({
                      ...current,
                      [key]: current[key].map((item, i) =>
                        i ===
                        (source.group === "rss"
                          ? index
                          : index - value.rss.length)
                          ? { ...item, enabled: event.target.checked }
                          : item,
                      ),
                    }));
                  }}
                />
              </td>
              <td>{source.name}</td>
              <td>{source.type || "rss"}</td>
              <td className="truncate">{source.url}</td>
              <td>
                <button className="button" onClick={() => onTest(source)}>
                  Test
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

const columnHelper = createColumnHelper<Result>();
function Results({ rows }: { rows: Result[] }) {
  const columns = useMemo(
    () => [
      columnHelper.accessor("title", {
        header: "Title",
        cell: (info) => (
          <a href={info.row.original.url} target="_blank">
            {info.getValue()}
          </a>
        ),
      }),
      columnHelper.accessor("source", { header: "Source" }),
      columnHelper.accessor("published", { header: "Published" }),
      columnHelper.display({
        id: "score",
        header: "Score",
        cell: (info) => info.row.original.ranking?.top_score ?? "—",
      }),
      columnHelper.display({
        id: "topics",
        header: "Topics",
        cell: (info) =>
          (info.row.original.categories || info.row.original.topics || []).join(
            ", ",
          ) || "—",
      }),
    ],
    [],
  );
  const table = useReactTable({
    data: rows,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });
  return (
    <section className="panel table-panel">
      <div className="panel-title">
        <span>{rows.length} results</span>
        <small>latest processed</small>
      </div>
      <table>
        <thead>
          {table.getHeaderGroups().map((group) => (
            <tr key={group.id}>
              {group.headers.map((header) => (
                <th key={header.id}>
                  {flexRender(
                    header.column.columnDef.header,
                    header.getContext(),
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
function Configuration({
  config,
  onSave,
  onNotice,
}: {
  config: Config;
  onSave: (value: Config) => void;
  onNotice: (message: string) => void;
}) {
  const [value, setValue] = useState(config);
  const [dirty, setDirty] = useState(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [modelFilter, setModelFilter] = useState("");
  const [loadingModels, setLoadingModels] = useState(false);
  const [statuses, setStatuses] = useState<Record<string, string>>({});
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({});
  useEffect(() => {
    if (!dirty) setValue(config);
  }, [config, dirty]);
  const set = (key: string, next: string | number | boolean) => {
    setDirty(true);
    setValue((current) => ({ ...current, [key]: next }));
  };
  const discover = useCallback(async () => {
    setLoadingModels(true);
    try {
      const data = await api<{
        models: ModelOption[];
        errors: Record<string, string>;
        credential_statuses: Record<string, string>;
      }>("/api/models?provider=all");
      setModels(data.models);
      setStatuses(data.credential_statuses);
      const failures = Object.keys(data.errors);
      onNotice(
        `${data.models.length} models loaded${failures.length ? `; unavailable: ${failures.join(", ")}` : ""}`,
      );
    } catch (error) {
      onNotice((error as Error).message);
    } finally {
      setLoadingModels(false);
    }
  }, [onNotice]);
  useEffect(() => {
    api<{ providers: Record<string, string> }>("/api/credentials/status")
      .then((data) => setStatuses(data.providers))
      .catch((error) => onNotice(error.message));
    discover();
  }, [discover, onNotice]);
  const saveCredential = async (provider: string) => {
    const apiKey = keyInputs[provider] || "";
    if (!apiKey) return;
    try {
      await api("/api/credentials", {
        method: "POST",
        body: JSON.stringify({ provider, api_key: apiKey }),
      });
      setKeyInputs((current) => ({ ...current, [provider]: "" }));
      setStatuses((current) => ({ ...current, [provider]: "configured" }));
      onNotice(`${provider} credential saved to the Windows user environment`);
      await discover();
    } catch (error) {
      setKeyInputs((current) => ({ ...current, [provider]: "" }));
      onNotice((error as Error).message);
    }
  };
  const selectedProvider = String(value.selected_provider || "nvidia");
  const visibleModels = models.filter(
    (model) =>
      (selectedProvider === "all" || model.provider === selectedProvider) &&
      `${model.name} ${model.id}`.toLowerCase().includes(modelFilter.toLowerCase()),
  );
  const numeric = [
    "global_concurrency",
    "per_domain_concurrency",
    "requests_per_minute",
    "request_timeout_seconds",
    "retry_limit",
    "retry_backoff_seconds",
    "freshness_hours",
    "retention_days",
    "refresh_seconds",
    "nvidia_temperature",
    "nvidia_top_p",
    "nvidia_max_tokens",
  ];
  return (
    <div className="config-layout">
      <section className="panel form-panel">
        <div className="panel-title">
          <span>Runtime</span>
          <button
            className="button primary"
            onClick={() => {
              onSave(value);
              setDirty(false);
            }}
          >
            {dirty ? "Save changes" : "Saved"}
          </button>
        </div>
        {numeric.slice(0, 9).map((key) => (
          <Field
            key={key}
            label={key.replaceAll("_", " ")}
            type="number"
            value={String(value[key] ?? "")}
            onChange={(next) => set(key, Number(next))}
          />
        ))}
      </section>
      <section className="panel form-panel">
        <div className="panel-title">
          <span>Models</span>
          <button className="button" disabled={loadingModels} onClick={discover}>
            {loadingModels ? "Loading" : "Refresh"}
          </button>
        </div>
        <label className="field">
          <span>Provider</span>
          <select
            value={selectedProvider}
            onChange={(event) => set("selected_provider", event.target.value)}
          >
            {["nvidia", "openrouter", "gemini", "featherless", "openai", "lm-studio", "vllm", "llama-cpp", "ollama-local"].map((provider) => (
              <option key={provider} value={provider}>{provider}</option>
            ))}
          </select>
        </label>
        <Field label="Filter models" value={modelFilter} onChange={setModelFilter} />
        <label className="field">
          <span>Model ({visibleModels.length})</span>
          <select
            value={String(value.selected_model || "")}
            onChange={(event) => set("selected_model", event.target.value)}
          >
            <option value="">Select a model</option>
            {visibleModels.map((model) => (
              <option key={`${model.provider}:${model.id}`} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </label>
        {numeric.slice(9).map((key) => (
          <Field
            key={key}
            label={key.replaceAll("_", " ")}
            type="number"
            value={String(value[key] ?? "")}
            onChange={(next) => set(key, Number(next))}
          />
        ))}
        <label className="check">
          <input
            type="checkbox"
            checked={Boolean(value.nvidia_thinking)}
            onChange={(event) => set("nvidia_thinking", event.target.checked)}
          />
          thinking
        </label>
        <div className="action-row">
          <button
            className="button"
            disabled={!value.selected_model}
            onClick={() =>
              api("/api/models/test", {
                method: "POST",
                body: JSON.stringify({
                  provider: value.selected_provider,
                  model: value.selected_model,
                }),
              })
                .then((data) => onNotice(JSON.stringify(data)))
                .catch((error) => onNotice(error.message))
            }
          >
            Test
          </button>
        </div>
      </section>
      <section className="panel credential-panel">
        <div className="panel-title"><span>Credentials</span><small>Windows user environment</small></div>
        {Object.entries({
          nvidia: "NVIDIA_API_KEY",
          openrouter: "OPENROUTER_API_KEY",
          gemini: "GEMINI_API_KEY",
          featherless: "FEATHERLESS_API_KEY",
          openai: "OPENAI_API_KEY",
        }).map(([provider, envName]) => (
          <div className="credential-row" key={provider}>
            <div><b>{provider}</b><small>{envName}</small></div>
            <Status value={statuses[provider] || "missing"} />
            <input
              type="password"
              autoComplete="off"
              placeholder="Paste replacement key"
              value={keyInputs[provider] || ""}
              onChange={(event) =>
                setKeyInputs((current) => ({ ...current, [provider]: event.target.value }))
              }
            />
            <button className="button" disabled={!keyInputs[provider]} onClick={() => saveCredential(provider)}>Save key</button>
          </div>
        ))}
      </section>
    </div>
  );
}

function Schedules({
  config,
  onSave,
}: {
  config: Config;
  onSave: (value: Config) => void;
}) {
  const [value, setValue] = useState(config);
  useEffect(() => setValue(config), [config]);
  return (
    <section className="panel form-panel">
      <div className="panel-title">
        <span>Schedule defaults</span>
        <button className="button primary" onClick={() => onSave(value)}>
          Save
        </button>
      </div>
      <Field
        label="Timezone"
        value={String(value.timezone || "America/New_York")}
        onChange={(timezone) => setValue((current) => ({ ...current, timezone }))}
      />
      <Field
        label="Planning days"
        type="number"
        value={String(value.plan_days || 60)}
        onChange={(plan_days) =>
          setValue((current) => ({ ...current, plan_days: Number(plan_days) }))
        }
      />
      <Field
        label="Items per day"
        type="number"
        value={String(value.plan_per_day || 4)}
        onChange={(plan_per_day) =>
          setValue((current) => ({ ...current, plan_per_day: Number(plan_per_day) }))
        }
      />
    </section>
  );
}

export default function App() {
  const [view, setView] = useState<View>("Overview");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [state, setState] = useState<State | null>(null);
  const [results, setResults] = useState<Result[]>([]);
  const [notice, setNotice] = useState("");
  const refresh = useCallback(async () => {
    try {
      const [dash, current, resultData] = await Promise.all([
        api<Dashboard>("/api/dashboard"),
        api<State>("/api/state"),
        api<{ results: Result[] }>("/api/results"),
      ]);
      setDashboard(dash);
      setState(current);
      setResults(resultData.results);
    } catch (error) {
      setNotice((error as Error).message);
    }
  }, []);
  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, [refresh]);
  const mutate = async (url: string, body: unknown) => {
    try {
      await api(url, { method: "PUT", body: JSON.stringify(body) });
      setNotice("Saved");
      await refresh();
    } catch (error) {
      setNotice((error as Error).message);
    }
  };
  const start = async () => {
    try {
      await api("/api/run", {
        method: "POST",
        body: JSON.stringify(state?.config || {}),
      });
      setView("Live run");
      refresh();
    } catch (error) {
      setNotice((error as Error).message);
    }
  };
  const failures = (dashboard?.events || []).filter(
    (event) => event.status === "error",
  );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="workspace">OPERATIONS</div>
        <nav>
          {nav.map((item) => (
            <button
              key={item}
              className={view === item ? "active" : ""}
              onClick={() => setView(item)}
            >
              {item}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <Status value={String(state?.run.status || "idle")} />
          <span>
            {dashboard?.credential_status === "configured"
              ? "NVIDIA ready"
              : "NVIDIA missing"}
          </span>
        </div>
      </aside>
      <main>
        <header className="command">
          <div>
            <b>{view}</b>
            <span>{state?.run.run_id?.slice(0, 8) || "No active run"}</span>
          </div>
          <div className="command-actions">
            <button className="button" onClick={refresh}>
              Refresh
            </button>
            <button
              className="button primary"
              disabled={state?.run.status === "running"}
              onClick={start}
            >
              Run
            </button>
          </div>
        </header>
        {notice && (
          <button className="notice" onClick={() => setNotice("")}>
            {notice}
          </button>
        )}
        <div className="content">
          {view === "Overview" && <Overview dashboard={dashboard} />}{" "}
          {view === "Live run" && (
            <LiveRun
              state={state}
              onCancel={() =>
                api("/api/run/cancel", { method: "POST" })
                  .then(refresh)
                  .catch((error) => setNotice(error.message))
              }
            />
          )}{" "}
          {view === "Categories" && (
            <Categories
              items={dashboard?.categories || []}
              onSave={(items) =>
                mutate("/api/categories", { categories: items })
              }
            />
          )}{" "}
          {view === "Sources" && state && (
            <Sources
              sources={state.sources}
              onSave={(sources) => mutate("/api/sources", sources)}
              onTest={(source) =>
                api("/api/sources/test", {
                  method: "POST",
                  body: JSON.stringify(source),
                })
                  .then((data) => setNotice(JSON.stringify(data)))
                  .catch((error) => setNotice(error.message))
              }
            />
          )}{" "}
          {view === "Results" && <Results rows={results} />}{" "}
          {view === "Failures" &&
            (failures.length ? (
              <EventList events={failures} />
            ) : (
              <Empty>No failures recorded.</Empty>
            ))}{" "}
          {view === "Traces" && (
            <EventList events={(dashboard?.events || []).slice().reverse()} />
          )}{" "}
          {view === "Schedules" && state && (
            <Schedules
              config={state.config}
              onSave={(config) => mutate("/api/config", config)}
            />
          )}{" "}
          {view === "Configuration" && state && (
            <Configuration
              config={state.config}
              onSave={(config) => mutate("/api/config", config)}
              onNotice={setNotice}
            />
          )}
        </div>
      </main>
    </div>
  );
}
