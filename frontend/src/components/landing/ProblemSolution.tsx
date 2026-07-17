import { IconPuzzle, IconRepeat, IconTrendingDown } from "../icons";
import { Reveal } from "./Reveal";

const PROBLEMS = [
  {
    Icon: IconPuzzle,
    title: "Lost project context",
    body: "Assistants forget your stack, decisions, and constraints the moment a session ends — so you re-explain everything.",
  },
  {
    Icon: IconRepeat,
    title: "Outdated instructions",
    body: "When you change your mind, the assistant keeps repeating the old plan and gives stale, contradictory advice.",
  },
  {
    Icon: IconTrendingDown,
    title: "Wasted context window",
    body: "Dumping full chat history burns tokens on irrelevant text and crowds out what actually matters.",
  },
];

const MEMORY_CAPABILITIES = [
  { title: "Memory Extraction", body: "Turns messages into structured, typed memory records." },
  { title: "Hybrid Retrieval", body: "Dense embeddings + keyword/tag search + structured filters." },
  { title: "Context Budget Manager", body: "Fits only the most relevant memories into a token budget." },
  { title: "Forgetting Engine", body: "Expires deadlines and archives stale, low-value memories." },
  { title: "Supersession Engine", body: "Replaces contradicted decisions with the latest one." },
  { title: "Memory Trace", body: "Explains exactly which memories were used, skipped, or forgotten." },
];

export function ProblemSolution() {
  return (
    <>
      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">
            AI assistants forget what matters.
          </h2>
          <p className="mt-3 text-slate-600">
            Standard chatbots only see recent history. That breaks down across
            sessions, decisions, and long projects.
          </p>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {PROBLEMS.map((p, i) => (
            <Reveal key={p.title} delay={i * 0.08}>
              <div className="glass card-hover h-full p-6">
                <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-rose-50 text-rose-500">
                  <p.Icon size={20} />
                </div>
                <h3 className="text-base font-semibold text-slate-800">{p.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{p.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="bg-gradient-to-b from-brand-50/40 to-transparent">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <div className="mx-auto mb-10 max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              Memory governance for smarter agents.
            </h2>
            <p className="mt-3 text-slate-600">
              A dedicated memory intelligence layer that decides what to keep,
              what to surface, and what to let go.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {MEMORY_CAPABILITIES.map((m, i) => (
              <Reveal key={m.title} delay={(i % 3) * 0.07}>
                <div className="glass card-hover flex h-full gap-3 p-5">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-brand-600 text-sm font-semibold text-white">
                    {i + 1}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-800">{m.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{m.body}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
