import { useState } from 'react';

const signals = [
  { title: 'OpenAI launches background mode for agents', source: 'OpenAI', score: 94, tag: 'Agent workflow' },
  { title: 'Remotion template patterns for data-led Shorts', source: 'GitHub', score: 89, tag: 'Video stack' },
  { title: 'Local model routing cuts batch cost', source: 'Hacker News', score: 84, tag: 'Local AI' },
];

const workflow = [
  { id: 'discover', label: 'Discover', detail: 'Scrape and rank signals', state: 'done' },
  { id: 'select', label: 'Select', detail: 'Choose one evidence-backed story', state: 'active' },
  { id: 'template', label: 'Template', detail: 'Shape hook, scenes, and CTA', state: 'next' },
  { id: 'render', label: 'Render', detail: 'Create a private review MP4', state: 'next' },
  { id: 'approve', label: 'Approve', detail: 'Human review before publishing', state: 'locked' },
];

export const SignalConsole = () => {
  const [view, setView] = useState<'signals' | 'workflow' | 'journal' | 'templates'>('signals');
  const [selected, setSelected] = useState(0);
  const [expanded, setExpanded] = useState<string | null>('select');
  const [note, setNote] = useState('');
  const [entries, setEntries] = useState(['Connected the local scraper to the YT Auto tool bridge.']);
  const [notice, setNotice] = useState('');

  const addEntry = () => {
    if (!note.trim()) return;
    setEntries((current) => [note.trim(), ...current]);
    setNote('');
    setNotice('Step saved');
  };

  return (
    <main className="min-h-screen w-full bg-[#101316] text-[#e8e5df] p-3 sm:p-5 lg:p-7">
      <div className="mx-auto max-w-[1440px] overflow-hidden rounded-[22px] border border-[#2a3035] bg-[#15191d] shadow-2xl shadow-black/30">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#2a3035] px-5 py-4 lg:px-7">
          <div className="flex items-center gap-3">
            <button onClick={() => setView('signals')} aria-label="Open signals" className="grid size-9 place-items-center rounded-xl bg-[#b9c9bd] text-sm font-semibold text-[#152018] transition hover:bg-[#d2ddd4]">S</button>
            <div><p className="text-sm font-semibold">Signal Console</p><p className="font-mono text-[10px] uppercase tracking-[.16em] text-[#7f8a91]">Scraper → Shorts</p></div>
          </div>
          <nav className="flex flex-wrap gap-1 rounded-xl bg-[#101316] p-1" aria-label="Workspace">
            {(['signals','workflow','journal','templates'] as const).map((item) => <button key={item} onClick={() => setView(item)} className={`rounded-lg px-3 py-2 text-xs capitalize transition ${view === item ? 'bg-[#252b30] text-[#f0ece5]' : 'text-[#89939a] hover:text-[#d6d2ca]'}`}>{item}</button>)}
          </nav>
          <div className="flex items-center gap-2"><span className="rounded-full border border-[#35423a] bg-[#17221b] px-2.5 py-1 font-mono text-[10px] text-[#9fc0a7]">● LOCAL READY</span><button onClick={() => setNotice('A safe dry run is ready to start')} className="rounded-xl bg-[#d2b59b] px-4 py-2 text-xs font-semibold text-[#241b15] transition hover:bg-[#e2c8b0]">New run</button></div>
        </header>

        {notice && <button onClick={() => setNotice('')} className="mx-5 mt-4 w-[calc(100%-2.5rem)] rounded-xl border border-[#424950] bg-[#20262b] px-4 py-2 text-left text-xs text-[#d8d3cb]">{notice} · dismiss</button>}

        {view === 'signals' && <section className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1.45fr)_minmax(300px,.55fr)] lg:p-7">
          <div>
            <div className="mb-7 flex flex-wrap items-end justify-between gap-4"><div><p className="mb-2 font-mono text-[10px] uppercase tracking-[.18em] text-[#82a6b5]">Today’s decision</p><h1 className="max-w-2xl text-3xl font-medium tracking-[-.035em] sm:text-4xl">Choose one signal worth turning into a Short.</h1></div><div className="flex gap-5 text-right"><div><strong className="block text-xl">20</strong><span className="text-[11px] text-[#7f8a91]">selected</span></div><div><strong className="block text-xl">5</strong><span className="text-[11px] text-[#7f8a91]">templates</span></div></div></div>
            <div className="space-y-2">{signals.map((signal, index) => <button key={signal.title} onClick={() => setSelected(index)} className={`grid w-full gap-4 rounded-2xl border p-4 text-left transition sm:grid-cols-[1fr_auto] ${selected === index ? 'border-[#667c86] bg-[#20272c]' : 'border-[#262c31] bg-[#181c20] hover:border-[#3b444a]'}`}><div><div className="mb-2 flex flex-wrap items-center gap-2"><span className="rounded-md bg-[#262d31] px-2 py-1 font-mono text-[9px] uppercase text-[#9fb0b8]">{signal.tag}</span><span className="text-[11px] text-[#747f86]">{signal.source}</span></div><h2 className="text-base font-medium sm:text-lg">{signal.title}</h2></div><div className="self-center text-right"><strong className="font-mono text-2xl text-[#b9c9bd]">{signal.score}</strong><span className="block text-[10px] text-[#747f86]">fit score</span></div></button>)}</div>
          </div>
          <aside className="rounded-2xl border border-[#2b3237] bg-[#181d21] p-5"><p className="font-mono text-[10px] uppercase tracking-[.16em] text-[#c0a68f]">Selected signal</p><h2 className="mt-3 text-xl font-medium">{signals[selected].title}</h2><div className="my-5 h-px bg-[#2c3338]"/><dl className="space-y-4 text-sm"><div><dt className="text-[11px] text-[#778188]">Recommended format</dt><dd>Evidence-led 30s explainer</dd></div><div><dt className="text-[11px] text-[#778188]">Template</dt><dd>Signal Brief / v1</dd></div><div><dt className="text-[11px] text-[#778188]">Approval gate</dt><dd>Review script and claims</dd></div></dl><button onClick={() => setView('templates')} className="mt-6 w-full rounded-xl bg-[#b9c9bd] px-4 py-3 text-sm font-semibold text-[#18211b] transition hover:bg-[#cfdbd1]">Build template</button><button onClick={() => setNotice('Signal saved to the review queue')} className="mt-2 w-full rounded-xl border border-[#343c42] px-4 py-3 text-sm text-[#bac1c5] transition hover:bg-[#22282d]">Save for later</button></aside>
        </section>}

        {view === 'workflow' && <section className="p-5 lg:p-7"><div className="mb-6"><p className="font-mono text-[10px] uppercase tracking-[.18em] text-[#82a6b5]">Automation map</p><h1 className="mt-2 text-3xl font-medium tracking-[-.03em]">See the workflow. Open only the step you need.</h1></div><div className="grid gap-2">{workflow.map((step, index) => <article key={step.id} className="rounded-2xl border border-[#293036] bg-[#181d21]"><button onClick={() => setExpanded(expanded === step.id ? null : step.id)} className="grid w-full grid-cols-[36px_1fr_auto] items-center gap-3 p-4 text-left"><span className={`grid size-8 place-items-center rounded-full font-mono text-xs ${step.state === 'done' ? 'bg-[#24362b] text-[#a9c8b1]' : step.state === 'active' ? 'bg-[#32414a] text-[#b8d4df]' : 'bg-[#23292e] text-[#858f95]'}`}>{index + 1}</span><span><b className="block text-sm font-medium">{step.label}</b><small className="text-[#778188]">{step.detail}</small></span><span className="font-mono text-xs text-[#778188]">{expanded === step.id ? '−' : '+'}</span></button>{expanded === step.id && <div className="border-t border-[#293036] px-16 py-4 text-sm text-[#9da6ac]">{step.state === 'locked' ? 'Publishing stays locked until an operator approves the final MP4 and metadata.' : 'Capture the manual actions here, then promote repeatable actions into a skill, webhook, or guarded MCP tool.'}</div>}</article>)}</div></section>}

        {view === 'journal' && <section className="grid gap-5 p-5 lg:grid-cols-[minmax(320px,.7fr)_1.3fr] lg:p-7"><div><p className="font-mono text-[10px] uppercase tracking-[.18em] text-[#c0a68f]">Tiny-step journal</p><h1 className="mt-2 text-3xl font-medium tracking-[-.03em]">Write it once. Spot the automation later.</h1><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Example: copied the approved title into YouTube Studio…" className="mt-6 min-h-36 w-full resize-none rounded-2xl border border-[#30383e] bg-[#111519] p-4 text-sm outline-none transition placeholder:text-[#59636a] focus:border-[#738791]"/><button onClick={addEntry} disabled={!note.trim()} className="mt-3 rounded-xl bg-[#d2b59b] px-4 py-3 text-sm font-semibold text-[#241b15] disabled:cursor-not-allowed disabled:opacity-40">Save step</button></div><div className="space-y-2">{entries.map((entry, index) => <details key={`${entry}-${index}`} className="rounded-2xl border border-[#293036] bg-[#181d21] p-4"><summary className="cursor-pointer text-sm font-medium">{entry}</summary><div className="mt-4 grid gap-3 border-t border-[#293036] pt-4 text-xs text-[#8f999f] sm:grid-cols-3"><button onClick={() => setNotice('Marked as repeatable')} className="rounded-lg border border-[#323a40] px-3 py-2 hover:bg-[#23292d]">Mark repeatable</button><button onClick={() => setNotice('Added to automation review')} className="rounded-lg border border-[#323a40] px-3 py-2 hover:bg-[#23292d]">Automation candidate</button><button onClick={() => setNotice('Attached to workflow')} className="rounded-lg border border-[#323a40] px-3 py-2 hover:bg-[#23292d]">Attach to step</button></div></details>)}</div></section>}

        {view === 'templates' && <section className="p-5 lg:p-7"><div className="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p className="font-mono text-[10px] uppercase tracking-[.18em] text-[#a9b99f]">Reusable output</p><h1 className="mt-2 text-3xl font-medium tracking-[-.03em]">Signal Brief / v1</h1></div><button onClick={() => setNotice('Template saved as a private draft')} className="rounded-xl bg-[#b9c9bd] px-4 py-3 text-sm font-semibold text-[#18211b]">Save template</button></div><div className="grid gap-4 lg:grid-cols-3">{[['Hook','This new agent feature changes what can run while you work.'],['Proof','Show the release source, one concrete capability, and one limitation.'],['CTA','Save this workflow and test it with a low-risk task.']].map(([label,value], index) => <details key={label} open={index === 0} className="rounded-2xl border border-[#2b3237] bg-[#181d21] p-5"><summary className="cursor-pointer font-mono text-[10px] uppercase tracking-[.14em] text-[#82a6b5]">{index + 1}. {label}</summary><p className="mt-4 text-sm leading-6 text-[#c7c5bf]">{value}</p></details>)}</div></section>}
      </div>
    </main>
  );
};
