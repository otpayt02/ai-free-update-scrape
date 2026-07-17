import { useState } from 'react';

const notes = [
  { time: '07:40', title: 'The small signal', text: 'One useful idea, gathered before the noise arrives.' },
  { time: '12:15', title: 'A kinder system', text: 'A two-minute ritual that makes tomorrow feel lighter.' },
  { time: '18:30', title: 'What remained', text: 'Three observations worth carrying into the next day.' },
];

export const SignalGardenLanding = () => {
  const [email, setEmail] = useState('');
  const [joined, setJoined] = useState(false);
  const [activeNote, setActiveNote] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (/\S+@\S+\.\S+/.test(email)) setJoined(true);
  };

  return (
    <main className="min-h-screen w-full overflow-hidden bg-[#f1eddf] text-[#17372d] selection:bg-[#ff6b3d] selection:text-white">
      <div className="mx-auto w-full max-w-[1440px] px-5 py-5 sm:px-8 lg:px-12">
        <nav className="flex items-center justify-between border-b border-[#17372d]/25 pb-5" aria-label="Primary navigation">
          <button className="flex items-center gap-3 text-left" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <span className="grid h-9 w-9 place-items-center rounded-full bg-[#ff6b3d] text-lg text-white">✦</span>
            <span className="font-serif text-xl font-semibold tracking-tight">Signal Garden</span>
          </button>
          <div className="hidden items-center gap-8 text-sm font-semibold md:flex">
            <a href="#field-notes" className="transition hover:text-[#ff5b2b]">Field notes</a>
            <a href="#method" className="transition hover:text-[#ff5b2b]">Our method</a>
            <a href="#join" className="rounded-full border border-[#17372d] px-5 py-2.5 transition hover:bg-[#17372d] hover:text-[#f1eddf]">Join the circle</a>
          </div>
          <button className="rounded-full border border-[#17372d] px-4 py-2 text-sm md:hidden" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen}>Menu</button>
        </nav>
        {menuOpen && <div className="flex flex-col gap-3 border-b border-[#17372d]/25 py-4 text-sm font-semibold md:hidden"><a href="#field-notes">Field notes</a><a href="#method">Our method</a><a href="#join">Join the circle</a></div>}

        <section className="grid min-h-[620px] items-center gap-10 py-14 lg:grid-cols-[1.08fr_.92fr] lg:py-20">
          <div className="relative z-10">
            <p className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#d8e3c5] px-4 py-2 text-xs font-bold uppercase tracking-[.18em]"><span className="h-2 w-2 rounded-full bg-[#ff6b3d]" /> A slower kind of intelligence</p>
            <h1 className="max-w-4xl font-serif text-[clamp(3.8rem,8.2vw,8rem)] font-medium leading-[.82] tracking-[-.065em]">Notice more.<br /><span className="italic text-[#ff5b2b]">Rush less.</span></h1>
            <p className="mt-8 max-w-xl text-lg leading-relaxed text-[#17372d]/75 sm:text-xl">A daily field note for curious people building thoughtful lives, creative work, and calmer systems.</p>
            <form id="join" onSubmit={submit} className="mt-9 flex max-w-xl flex-col gap-3 sm:flex-row">
              {joined ? <div className="w-full rounded-2xl bg-[#17372d] px-6 py-4 font-semibold text-[#f1eddf]">You’re in. Your first signal arrives tomorrow morning. ✦</div> : <><label className="sr-only" htmlFor="garden-email">Email address</label><input id="garden-email" required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@yourcorner.world" className="min-w-0 flex-1 rounded-full border border-[#17372d]/40 bg-white/45 px-6 py-4 outline-none transition placeholder:text-[#17372d]/45 focus:border-[#ff5b2b] focus:ring-4 focus:ring-[#ff6b3d]/15" /><button className="rounded-full bg-[#17372d] px-7 py-4 font-bold text-[#f1eddf] transition hover:-translate-y-0.5 hover:bg-[#ff5b2b] active:translate-y-0">Get the note →</button></>}
            </form>
            <p className="mt-3 text-xs text-[#17372d]/55">Free forever · Read in under four minutes · No feed to refresh</p>
          </div>

          <div className="relative mx-auto flex min-h-[470px] w-full max-w-[560px] items-center justify-center" aria-label="Illustrated field note preview">
            <div className="absolute inset-[8%] rounded-[48%_52%_42%_58%/55%_38%_62%_45%] bg-[#bdcf9d]" />
            <div className="absolute left-[8%] top-[8%] h-24 w-24 rounded-full border border-[#17372d]/30" />
            <div className="absolute bottom-[8%] right-[5%] h-36 w-36 rounded-full bg-[#ff6b3d]" />
            <article className="relative w-[76%] rotate-[-3deg] border border-[#17372d]/35 bg-[#fffaf0] p-7 shadow-[12px_14px_0_#17372d] transition duration-500 hover:rotate-0 sm:p-9">
              <div className="mb-12 flex justify-between border-b border-[#17372d]/25 pb-3 text-[10px] font-bold uppercase tracking-[.2em]"><span>Field Note 024</span><span>Friday</span></div>
              <p className="font-serif text-3xl leading-tight sm:text-4xl">“Attention is how a place becomes a world.”</p>
              <div className="mt-12 flex items-end justify-between"><div><p className="text-xs uppercase tracking-[.18em]">Today’s practice</p><p className="mt-1 font-semibold">Take the long way home.</p></div><span className="text-3xl">↗</span></div>
            </article>
          </div>
        </section>

        <section id="field-notes" className="border-t border-[#17372d]/25 py-12 lg:grid lg:grid-cols-[.38fr_.62fr] lg:gap-16">
          <div><p className="text-xs font-bold uppercase tracking-[.2em] text-[#ff5b2b]">Three signals a day</p><h2 className="mt-4 max-w-sm font-serif text-4xl leading-tight sm:text-5xl">A rhythm for paying attention.</h2></div>
          <div id="method" className="mt-8 grid gap-3 lg:mt-0">
            {notes.map((note, index) => <button key={note.time} onClick={() => setActiveNote(index)} className={`grid grid-cols-[64px_1fr_auto] items-center gap-4 rounded-2xl border p-5 text-left transition ${activeNote === index ? 'border-[#17372d] bg-[#17372d] text-[#f1eddf]' : 'border-[#17372d]/20 hover:border-[#ff5b2b] hover:bg-white/35'}`} aria-pressed={activeNote === index}><span className="font-mono text-xs">{note.time}</span><span><strong className="block font-serif text-xl">{note.title}</strong><span className={`mt-1 block text-sm ${activeNote === index ? 'text-[#f1eddf]/70' : 'text-[#17372d]/65'}`}>{note.text}</span></span><span className="text-2xl">{activeNote === index ? '●' : '○'}</span></button>)}
          </div>
        </section>
      </div>
    </main>
  );
};
