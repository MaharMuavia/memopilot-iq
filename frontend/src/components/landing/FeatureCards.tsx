import {
  IconLayers, IconLink, IconHourglass, IconPin, IconTarget,
  IconTrace, IconGauge, IconEval,
} from "../icons";
import { Reveal } from "./Reveal";

const FEATURES = [
  {
    Icon: IconLayers,
    title: "Persistent Memory",
    body: "Structured memory records persist across sessions in SQLite or Alibaba Cloud Tablestore.",
  },
  {
    Icon: IconLink,
    title: "Cross-Session Recall",
    body: "Preferences and decisions from earlier sessions resurface exactly when they are relevant.",
  },
  {
    Icon: IconHourglass,
    title: "Timely Forgetting",
    body: "Deadlines expire and unused, low-value memories archive automatically — non-destructively.",
  },
  {
    Icon: IconPin,
    title: "Critical Memory Pinning",
    body: "Critical rules are considered first while a strict context budget prevents prompt bloat.",
  },
  {
    Icon: IconTarget,
    title: "Limited Context Retrieval",
    body: "A scoring formula + token budget inject only the highest-value memories into the prompt.",
  },
  {
    Icon: IconTrace,
    title: "Transparent Memory Trace",
    body: "Every answer shows which memories were used, skipped, superseded, or forgotten — and why.",
  },
  {
    Icon: IconGauge,
    title: "Context Budget Manager",
    body: "A token budget injects only the highest-value memories and reports the tokens saved.",
  },
  {
    Icon: IconEval,
    title: "Evaluation Benchmark",
    body: "Built-in scenarios score the memory agent against a no-memory baseline on recall and accuracy.",
  },
];

export function FeatureCards() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-4 py-16">
      <div className="mx-auto mb-10 max-w-2xl text-center">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
          A memory layer any agent can plug into
        </h2>
        <p className="mt-3 text-slate-600">
          Six capabilities that turn a stateless chatbot into a self-curating
          assistant.
        </p>
      </div>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <Reveal key={f.title} delay={(i % 3) * 0.06}>
            <div className="glass card-hover h-full p-6">
              <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600">
                <f.Icon size={20} />
              </div>
              <h3 className="text-base font-semibold text-slate-800">{f.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{f.body}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
