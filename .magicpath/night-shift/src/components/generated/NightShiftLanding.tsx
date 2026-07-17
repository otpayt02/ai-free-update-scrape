import { useState } from 'react';

const modes = {
  focus: { label: 'FOCUS', time: '42:18', status: 'Deep work window', color: '#b8ff5a' },
  sprint: { label: 'SPRINT', time: '18:00', status: 'Ship one clear outcome', color: '#ff6bda' },
  reset: { label: 'RESET', time: '05:00', status: 'Step away from the screen', color: '#67e8f9' },
};

export const NightShiftLanding = () => {
  const [mode, setMode] = useState<keyof typeof modes>('focus');
  const [running, setRunning] = useState(false);
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [menu, setMenu] = useState(false);
  const active = modes[mode];

  return (
    <main className="min-h-screen w-full overflow-hidden bg-[#07080b] text-[#f4f2ea] selection:bg-[#b8ff5a] selection:text-black">
      <div className="pointer-events-none absolute inset-0 opacity-[.18]" style={{backgroundImage:'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px),linear-gradient(90deg,rgba(255,255,255,.1) 1px,transparent 1px)',backgroundSize:'48px 48px'}} />
      <div className="relative mx-auto w-full max-w-[1440px] px-5 py-5 sm:px-8 lg:px-12">
        <nav className="flex items-center justify-between border-b border-white/15 pb-5">
          <button onClick={() => window.scrollTo({top:0,behavior:'smooth'})} className="flex items-center gap-3 font-mono text-sm font-bold tracking-[.18em]"><span className="grid h-9 w-9 place-items-center bg-[#b8ff5a] text-black">N/</span>NIGHTSHIFT</button>
          <div className="hidden items-center gap-7 font-mono text-xs text-white/65 md:flex"><a href="#protocol" className="hover:text-[#b8ff5a]">PROTOCOL</a><a href="#access" className="hover:text-[#b8ff5a]">EARLY ACCESS</a><span className="flex items-center gap-2 text-[#b8ff5a]"><span className="h-2 w-2 animate-pulse rounded-full bg-current" />SYSTEM ONLINE</span></div>
          <button onClick={() => setMenu(!menu)} className="border border-white/25 px-3 py-2 font-mono text-xs md:hidden" aria-expanded={menu}>MENU_</button>
        </nav>
        {menu && <div className="flex justify-between border-b border-white/15 py-4 font-mono text-xs"><a href="#protocol">PROTOCOL</a><a href="#access">EARLY ACCESS</a></div>}

        <section className="grid min-h-[680px] items-center gap-12 py-14 lg:grid-cols-[1.06fr_.94fr] lg:py-20">
          <div>
            <p className="mb-6 font-mono text-xs tracking-[.2em] text-[#b8ff5a]">// PERSONAL OPERATING SYSTEM · V0.9</p>
            <h1 className="max-w-4xl text-[clamp(4rem,9vw,8.7rem)] font-black uppercase leading-[.76] tracking-[-.075em]">Own<br />the <span className="text-transparent [-webkit-text-stroke:2px_#f4f2ea]">hours</span><span className="text-[#b8ff5a]">.</span></h1>
            <p className="mt-9 max-w-xl text-lg leading-relaxed text-white/62 sm:text-xl">NightShift turns scattered ambition into focused sessions, clean shutdowns, and work you can actually point to.</p>
            <div className="mt-9 flex flex-wrap gap-3"><a href="#access" className="bg-[#b8ff5a] px-7 py-4 font-mono text-sm font-bold text-black transition hover:-translate-y-1 hover:shadow-[6px_6px_0_#f4f2ea]">REQUEST ACCESS ↗</a><button onClick={() => setRunning(!running)} className="border border-white/30 px-7 py-4 font-mono text-sm transition hover:border-white">{running ? 'PAUSE DEMO ■' : 'RUN DEMO ▶'}</button></div>
          </div>

          <div className="relative mx-auto w-full max-w-[560px] border border-white/20 bg-[#0e1016] p-3 shadow-[0_0_80px_rgba(184,255,90,.1)]">
            <div className="flex items-center justify-between border-b border-white/15 px-3 py-3 font-mono text-[10px] text-white/45"><span>SESSION.CONTROL</span><span>LOCAL / PRIVATE</span></div>
            <div className="p-5 sm:p-8">
              <div className="flex gap-2">{(Object.keys(modes) as Array<keyof typeof modes>).map(key => <button key={key} onClick={() => {setMode(key);setRunning(false)}} className={`flex-1 border px-2 py-3 font-mono text-[10px] font-bold transition ${mode === key ? 'border-transparent text-black' : 'border-white/15 text-white/45 hover:text-white'}`} style={mode === key ? {backgroundColor:modes[key].color} : {}}>{modes[key].label}</button>)}</div>
              <div className="my-10 text-center"><p className="font-mono text-[clamp(4rem,9vw,7rem)] font-light leading-none tracking-[-.08em]" style={{color:active.color}}>{running ? active.time : active.time}</p><p className="mt-3 font-mono text-xs tracking-[.18em] text-white/42">{running ? '● SESSION ACTIVE' : active.status.toUpperCase()}</p></div>
              <button onClick={() => setRunning(!running)} className="w-full py-4 font-mono text-sm font-black text-black transition hover:brightness-110 active:scale-[.99]" style={{backgroundColor:active.color}}>{running ? 'PAUSE SESSION' : 'START SESSION'}</button>
              <div className="mt-5 grid grid-cols-3 gap-2 text-center font-mono text-[10px] text-white/45"><div className="border border-white/10 p-3"><strong className="block text-base text-white">08</strong>STREAK</div><div className="border border-white/10 p-3"><strong className="block text-base text-white">14.2h</strong>FOCUS</div><div className="border border-white/10 p-3"><strong className="block text-base text-white">93%</strong>DONE</div></div>
            </div>
            <div className="absolute -right-4 -top-4 h-12 w-12 border-r-2 border-t-2" style={{borderColor:active.color}} />
            <div className="absolute -bottom-4 -left-4 h-12 w-12 border-b-2 border-l-2" style={{borderColor:active.color}} />
          </div>
        </section>

        <section id="protocol" className="grid gap-px border border-white/15 bg-white/15 md:grid-cols-3">
          {[['01','DEFINE','Choose the single outcome that makes this session count.'],['02','EXECUTE','Block the noise. Work against a visible, honest clock.'],['03','CLOSE','Log what shipped and leave tomorrow a clean starting point.']].map(item => <article key={item[0]} className="bg-[#07080b] p-7 transition hover:bg-[#10131a] sm:p-9"><span className="font-mono text-xs text-[#b8ff5a]">{item[0]} //</span><h2 className="mt-10 text-3xl font-black tracking-tight">{item[1]}</h2><p className="mt-3 leading-relaxed text-white/52">{item[2]}</p></article>)}
        </section>

        <section id="access" className="my-12 flex flex-col gap-8 border border-white/15 bg-[#10131a] p-6 sm:p-10 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-mono text-xs text-[#ff6bda]">// LIMITED BETA</p><h2 className="mt-2 text-3xl font-black sm:text-4xl">Make the next hour yours.</h2></div>{sent ? <p className="font-mono text-[#b8ff5a]">ACCESS REQUEST LOGGED ✓</p> : <form onSubmit={e=>{e.preventDefault();if(/\S+@\S+\.\S+/.test(email))setSent(true)}} className="flex w-full max-w-xl flex-col gap-2 sm:flex-row"><label htmlFor="night-email" className="sr-only">Email address</label><input id="night-email" required type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="OPERATOR@EMAIL.COM" className="min-w-0 flex-1 border border-white/20 bg-black/30 px-5 py-4 font-mono text-sm outline-none placeholder:text-white/25 focus:border-[#b8ff5a]"/><button className="bg-[#f4f2ea] px-6 py-4 font-mono text-sm font-bold text-black hover:bg-[#b8ff5a]">JOIN WAITLIST</button></form>}</section>
      </div>
    </main>
  );
};
