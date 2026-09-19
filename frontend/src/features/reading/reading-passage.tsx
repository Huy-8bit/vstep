"use client";
import { useEffect, useRef } from "react";
import { PracticeAssets } from "@/features/library/practice-assets";
import { topics, type ReadingPassage as Passage } from "./types";
export function ReadingPassage({
  passage,
  highlight,
  onTerm,
}: {
  passage: Passage;
  highlight?: string | null;
  onTerm?: (term: string, paragraph: string) => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (highlight)
      root.current
        ?.querySelector(`[data-paragraph="${highlight}"]`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    else root.current?.scrollTo({ top: 0 });
  }, [passage.id, highlight]);
  return (
    <div
      ref={root}
      className="h-full overflow-y-auto overscroll-contain px-5 py-6 sm:px-8"
      aria-label="Bài đọc"
    >
      <p className="eyebrow">
        {topics[passage.topic] || passage.topic} · {passage.word_count} từ
      </p>
      <h2 className="mb-7 mt-3 text-2xl font-bold leading-relaxed">
        {passage.title}
      </h2>
      <PracticeAssets ids={passage.practice_asset_ids} />
      <div className="space-y-6">
        {passage.paragraphs.map((p, i) => (
          <div
            key={p.id}
            data-paragraph={p.id}
            className={`rounded-lg transition-colors ${highlight === p.id ? "bg-amber-100 p-4 ring-2 ring-amber-300" : ""}`}
          >
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              Paragraph {i + 1}
              {highlight === p.id ? " · Bằng chứng" : ""}
            </p>
            <p
              className="whitespace-pre-wrap text-[17px] leading-[1.95] text-stone-700"
              onMouseUp={() => {
                if (!onTerm) return;
                const selection = window.getSelection();
                const text = selection?.toString().trim();
                const paragraphNode = root.current?.querySelector(
                  `[data-paragraph="${p.id}"]`,
                );
                if (
                  text &&
                  text.length <= 100 &&
                  paragraphNode?.contains(selection?.anchorNode || null) &&
                  paragraphNode?.contains(selection?.focusNode || null)
                )
                  onTerm(text, p.id);
              }}
            >
              {onTerm
                ? p.text.split(/(\s+)/).map((word, n) =>
                    /\s/.test(word) ? (
                      word
                    ) : (
                      <span
                        key={n}
                        className="cursor-pointer rounded hover:bg-teal-100"
                        onClick={() => {
                          if (window.getSelection()?.toString().trim()) return;
                          const cleaned = word.replace(
                            /^[^a-zA-Z]+|[^a-zA-Z]+$/g,
                            "",
                          );
                          if (cleaned) onTerm(cleaned, p.id);
                        }}
                      >
                        {word}
                      </span>
                    ),
                  )
                : p.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
