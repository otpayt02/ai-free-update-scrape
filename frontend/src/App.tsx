import { useCallback, useEffect, useMemo, useState } from "react";

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

type Dashboard = {
  run: { finished_at?: string; started_at?: string };
};

type State = {
  run: { status: string };
};

type Decision = "relevant" | "ignored" | "sheets";
type TimeFilter = "today" | "3days" | "week";
type SortMode = "recent" | "relevance";

const categories = ["Models", "Tools", "Infra", "Policy", "Business"];
const tagOptions = ["Free/open-source", "Local", "Reasoning", "Cloud", "Storage/KB"];

const api = async <T,>(url: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
};

function categoryFor(item: Result): string {
  const text = `${item.categories?.join(" ")} ${item.topics?.join(" ")} ${item.title}`.toLowerCase();
  if (/policy|regulat|safety|law/.test(text)) return "Policy";
  if (/business|funding|enterprise|pricing/.test(text)) return "Business";
  if (/infra|gpu|cloud|database|storage|vector/.test(text)) return "Infra";
  if (/tool|agent|sdk|api|workflow|assistant/.test(text)) return "Tools";
  return "Models";
}

function tagsFor(item: Result): string[] {
  const text = `${item.title} ${item.categories?.join(" ")} ${item.topics?.join(" ")} ${item.detection?.type || ""}`.toLowerCase();
  return tagOptions.filter((tag) => {
    if (tag === "Free/open-source") return /free|open.source|github|self.host/.test(text);
    if (tag === "Local") return /local|on.device|edge|offline/.test(text);
    if (tag === "Reasoning") return /reason|thinking|chain.of.thought/.test(text);
    if (tag === "Cloud") return /cloud|hosted|api|context/.test(text);
    return /storage|knowledge base|\bkb\b|vector|memory/.test(text);
  });
}

function scoreFor(item: Result): number {
  return Number(item.ranking?.top_score || 0);
}

function fitFor(item: Result): "Strong" | "Medium" | "Weak" {
  const score = scoreFor(item);
  if (score >= 0.7) return "Strong";
  if (score >= 0.4) return "Medium";
  return "Weak";
}

function coverageFor(item: Result): "Low" | "Medium" | "High" {
  const count = (item.categories?.length || 0) + (item.topics?.length || 0) + tagsFor(item).length;
  if (count >= 6) return "High";
  if (count >= 3) return "Medium";
  return "Low";
}

function itemKey(item: Result): string {
  return item.url || `${item.source}-${item.title}`;
}

function Header({ lastScrape, running, onRun }: { lastScrape?: string; running: boolean; onRun: () => void }) {
  return <header className="topbar"><div><h1>AI Free Stacker</h1><span>Last scrape: {lastScrape ? new Date(lastScrape).toLocaleString() : "Not available"}</span></div><button className="primary" disabled={running} onClick={onRun}>{running ? "Running…" : "Run new scrape"}</button></header>;
}

function Filters({ time, setTime, selectedCategories, toggleCategory, selectedTags, toggleTag }: { time: TimeFilter; setTime: (value: TimeFilter) => void; selectedCategories: string[]; toggleCategory: (value: string) => void; selectedTags: string[]; toggleTag: (value: string) => void }) {
  return <aside className="filters"><FilterGroup label="Time">{[["Today", "today"], ["Last 3 days", "3days"], ["Last week", "week"]].map(([label, value]) => <button key={value} className={time === value ? "selected" : ""} onClick={() => setTime(value as TimeFilter)}>{label}</button>)}</FilterGroup><FilterGroup label="Category">{categories.map((value) => <button key={value} className={selectedCategories.includes(value) ? "selected" : ""} onClick={() => toggleCategory(value)}>{value}</button>)}</FilterGroup><FilterGroup label="Tags">{tagOptions.map((value) => <button key={value} className={selectedTags.includes(value) ? "selected" : ""} onClick={() => toggleTag(value)}>{value}</button>)}</FilterGroup></aside>;
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return <section><h2>{label}</h2><div>{children}</div></section>;
}

function ResultsList({ items, decisions, onDecision }: { items: Result[]; decisions: Record<string, Decision>; onDecision: (item: Result, value: Decision) => void }) {
  return <div className="table-wrap"><table><thead><tr><th>Update</th><th>Source</th><th>Published</th><th>Category</th><th>Tags</th><th>Fit</th><th>Coverage</th><th>Actions</th></tr></thead><tbody>{items.map((item) => { const key = itemKey(item); const tags = tagsFor(item); return <tr key={key}><td className="title-cell"><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a></td><td>{item.source || "Unknown"}</td><td className="nowrap">{item.published ? new Date(item.published).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "—"}</td><td>{categoryFor(item)}</td><td><div className="tags">{tags.length ? tags.map((tag) => <span key={tag}>{tag}</span>) : <span>—</span>}</div></td><td><span className={`signal ${fitFor(item).toLowerCase()}`}>{fitFor(item)}</span></td><td>{coverageFor(item)}</td><td><div className="actions"><button className={decisions[key] === "relevant" ? "active" : ""} onClick={() => onDecision(item, "relevant")}>Relevant</button><button className={decisions[key] === "ignored" ? "active danger" : ""} onClick={() => onDecision(item, "ignored")}>Ignore</button><button className={decisions[key] === "sheets" ? "active" : ""} onClick={() => onDecision(item, "sheets")}>Send to Sheets</button></div></td></tr>; })}</tbody></table>{!items.length && <div className="empty">No updates match these filters.</div>}</div>;
}

function SelectedPanel({ items, decisions }: { items: Result[]; decisions: Record<string, Decision> }) {
  const queued = items.filter((item) => ["relevant", "sheets"].includes(decisions[itemKey(item)]));
  return <aside className="queue"><div className="queue-title"><h2>Selected</h2><span>{queued.length}</span></div>{queued.map((item) => <article key={itemKey(item)}><strong>{item.title}</strong><small>{categoryFor(item)} · {tagsFor(item).join(", ") || "No tags"}</small><span>{decisions[itemKey(item)] === "sheets" ? "Sheets" : "Relevant"}</span></article>)}{!queued.length && <p>Nothing selected.</p>}</aside>;
}

export default function App() {
  const [items, setItems] = useState<Result[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [state, setState] = useState<State | null>(null);
  const [time, setTime] = useState<TimeFilter>("week");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [sort, setSort] = useState<SortMode>("recent");
  const [decisions, setDecisions] = useState<Record<string, Decision>>(() => JSON.parse(localStorage.getItem("triage-decisions") || "{}"));
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [results, dash, current] = await Promise.all([api<{ results: Result[] }>("/api/results"), api<Dashboard>("/api/dashboard"), api<State>("/api/state")]);
      setItems(results.results); setDashboard(dash); setState(current);
    } catch (error) { setNotice((error as Error).message); }
  }, []);

  useEffect(() => { refresh(); const timer = setInterval(refresh, 10000); return () => clearInterval(timer); }, [refresh]);
  useEffect(() => { localStorage.setItem("triage-decisions", JSON.stringify(decisions)); }, [decisions]);
  useEffect(() => { if (!notice) return; const timer = setTimeout(() => setNotice(""), 1800); return () => clearTimeout(timer); }, [notice]);

  const run = async () => {
    try { await api("/api/run", { method: "POST", body: JSON.stringify({}) }); setNotice("Scrape started"); await refresh(); } catch (error) { setNotice((error as Error).message); }
  };
  const toggle = (value: string, list: string[], setter: (next: string[]) => void) => setter(list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);
  const onDecision = (item: Result, value: Decision) => setDecisions((current) => {
    const next = { ...current };
    if (next[itemKey(item)] === value) delete next[itemKey(item)];
    else next[itemKey(item)] = value;
    return next;
  });
  const visible = useMemo(() => {
    const hours = time === "today" ? 24 : time === "3days" ? 72 : 168;
    const cutoff = Date.now() - hours * 60 * 60 * 1000;
    return items.filter((item) => !item.published || new Date(item.published).getTime() >= cutoff).filter((item) => !selectedCategories.length || selectedCategories.includes(categoryFor(item))).filter((item) => !selectedTags.length || selectedTags.some((tag) => tagsFor(item).includes(tag))).sort((a, b) => sort === "relevance" ? scoreFor(b) - scoreFor(a) : new Date(b.published || 0).getTime() - new Date(a.published || 0).getTime());
  }, [items, time, selectedCategories, selectedTags, sort]);

  return <><Header lastScrape={dashboard?.run.finished_at || dashboard?.run.started_at} running={state?.run.status === "running"} onRun={run} />{notice && <div className="notice">{notice}</div>}<div className="layout"><Filters time={time} setTime={setTime} selectedCategories={selectedCategories} toggleCategory={(value) => toggle(value, selectedCategories, setSelectedCategories)} selectedTags={selectedTags} toggleTag={(value) => toggle(value, selectedTags, setSelectedTags)} /><main><div className="results-head"><div><h2>Latest updates</h2><span>{visible.length} items</span></div><label>Sort<select value={sort} onChange={(event) => setSort(event.target.value as SortMode)}><option value="recent">Most recent</option><option value="relevance">Relevance</option></select></label></div><ResultsList items={visible} decisions={decisions} onDecision={onDecision} /></main><SelectedPanel items={items} decisions={decisions} /></div></>;
}
