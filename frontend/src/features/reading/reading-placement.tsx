import type { ReadingQuestion, ReadingPassage } from "./types";

export function ReadingPlacement({
  question,
  passage,
}: {
  question: ReadingQuestion;
  passage: ReadingPassage;
}) {
  const placement = question.placement;
  if (!placement) return null;
  const paragraph = passage.paragraphs.find(
    (p) => p.id === placement.paragraph_id,
  );
  if (!paragraph) return null;
  const ends = placement.positions.map(
    (position) =>
      paragraph.text.indexOf(position.after_text) + position.after_text.length,
  );
  const fragments = placement.positions.map((position, i) => {
    const text = paragraph.text.slice(i ? ends[i - 1] : 0, ends[i]);
    return (
      <span key={position.label}>
        {text}
        <strong className="mx-2 inline-block rounded bg-teal-100 px-2 text-teal-900">
          [{position.label}]
        </strong>
      </span>
    );
  });
  return (
    <div className="my-5 space-y-3 rounded-xl border border-stone-200 bg-stone-50 p-4 text-sm leading-7">
      <p className="text-xs font-semibold text-stone-500">
        {placement.paragraph_id} · Insertion positions
      </p>
      {placement.sentence_to_insert && (
        <blockquote
          lang="en"
          className="border-l-2 border-teal-600 pl-3 font-semibold"
        >
          {placement.sentence_to_insert}
        </blockquote>
      )}
      <p lang="en">
        {fragments}
        {paragraph.text.slice(ends.at(-1) || 0)}
      </p>
    </div>
  );
}
