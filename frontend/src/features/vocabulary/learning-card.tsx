"use client";
import Link from "next/link";
import { useState } from "react";
import { BookmarkPlus, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { post } from "@/services/api";
import type { LearningItem, Suggestion, VocabularyItem } from "./types";

export function LearningContent({
  item,
  original,
  improved,
}: {
  item: LearningItem;
  original?: string | null;
  improved?: string | null;
}) {
  return (
    <div className="space-y-4 text-sm leading-7">
      <div>
        <h3 lang="en" className="text-xl font-bold text-teal-900">
          {item.phrase}
        </h3>
        <p className="text-xs text-stone-500">
          {item.part_of_speech} · {item.register}
        </p>
      </div>
      {original && (
        <div className="rounded-xl bg-stone-50 p-4">
          <p className="text-xs font-semibold text-stone-500">Từ bài của bạn</p>
          <p lang="en" className="whitespace-pre-wrap">
            {original}
          </p>
          {improved && (
            <>
              <p className="mt-2 text-xs font-semibold text-teal-700">
                Cách diễn đạt tự nhiên
              </p>
              <p lang="en">{improved}</p>
            </>
          )}
        </div>
      )}
      <div>
        <p className="font-semibold">{item.meaning_vi}</p>
        <p className="text-stone-600">{item.meaning_in_context_vi}</p>
      </div>
      <div>
        <p className="text-xs font-semibold text-stone-500">Cụm từ đi cùng</p>
        <p lang="en">{item.collocations.join(" · ")}</p>
      </div>
      <div>
        <p className="text-xs font-semibold text-stone-500">Cách dùng</p>
        {item.common_patterns.map((p) => (
          <p key={p} lang="en">
            {p}
          </p>
        ))}
      </div>
      <blockquote
        lang="en"
        className="border-l-2 border-teal-600 pl-4 italic text-stone-700"
      >
        {item.example_sentence}
      </blockquote>
      <p className="text-xs text-stone-500">{item.why_learn_this_vi}</p>
    </div>
  );
}
export function SuggestionCard({
  item,
  batchId,
}: {
  item: Suggestion;
  batchId: string;
}) {
  const [saved, setSaved] = useState(item.saved_item_id);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save() {
    setBusy(true);
    setError("");
    try {
      const result = await post<VocabularyItem>("/vocabulary/items", {
        batch_id: batchId,
        item_index: item.index,
      });
      setSaved(result.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="panel p-5 sm:p-6">
      <LearningContent
        item={item}
        original={item.user_original}
        improved={item.better_version}
      />
      {item.natural_options.length > 1 && (
        <p lang="en" className="mt-4 text-xs text-stone-500">
          {item.natural_options.join(" / ")}
        </p>
      )}
      {error && <ErrorNotice message={error} />}
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <Button
          size="sm"
          variant="outline"
          disabled={busy || !!saved}
          onClick={save}
        >
          {saved ? <Check /> : <BookmarkPlus />}
          {saved ? "Đã lưu" : busy ? "Đang lưu..." : "Lưu để ôn"}
        </Button>
        {saved && (
          <Link
            href="/vocabulary"
            className="text-xs font-semibold text-teal-700"
          >
            Mở sổ từ vựng →
          </Link>
        )}
      </div>
    </article>
  );
}
