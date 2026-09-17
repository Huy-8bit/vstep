export function IdeaMap({ topic, ideas }: { topic: string; ideas: string[] }) {
  return (
    <section
      lang="en"
      className="mt-6 rounded-2xl border border-stone-200 bg-stone-50 p-5"
      aria-label="Topic development idea map"
    >
      <p className="text-center text-xs font-semibold tracking-wider text-stone-500">
        SUGGESTED IDEAS
      </p>
      <div className="mx-auto mt-4 max-w-md rounded-xl bg-teal-800 px-5 py-4 text-center text-sm font-semibold leading-6 text-white">
        {topic}
      </div>
      <div className="mx-auto h-6 w-px bg-teal-300" aria-hidden="true" />
      <ul className="relative grid gap-3 border-t border-teal-300 pt-4 sm:grid-cols-2">
        {[...ideas, "Your own ideas"].map((idea, i) => (
          <li
            key={idea}
            className={`rounded-xl border px-4 py-3 text-center text-sm leading-6 ${i === ideas.length ? "border-dashed border-teal-500 bg-teal-50" : "border-stone-200 bg-white"}`}
          >
            {idea}
          </li>
        ))}
      </ul>
    </section>
  );
}
