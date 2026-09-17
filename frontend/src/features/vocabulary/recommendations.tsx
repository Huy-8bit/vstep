"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { post } from "@/services/api";
import { SuggestionCard } from "./learning-card";
import type { Batch, Source, Review } from "./types";

const groups = [
  {
    title: "Cụm từ bạn dùng chưa tự nhiên",
    types: ["UNNATURAL_EXPRESSION", "SPOKEN_EXPRESSION"],
  },
  {
    title: "Từ / cụm từ nên biết cho chủ đề này",
    types: ["TOPIC", "READING_CONTEXT"],
  },
  { title: "Lỗi từ vựng lặp lại", types: ["REPEATED_ERROR"] },
];
export function VocabularyRecommendations({ source }: { source: Source }) {
  return <RecommendationList key={JSON.stringify(source)} source={source} />;
}
function RecommendationList({ source }: { source: Source }) {
  const [batch, setBatch] = useState<Batch | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const key = JSON.stringify(source);
  useEffect(() => {
    let active = true;
    post<Batch>("/vocabulary/recommendations?generate=false", JSON.parse(key))
      .then((b) => {
        if (active) setBatch(b);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [key]);
  async function generate() {
    setBusy(true);
    setError("");
    try {
      setBatch(await post<Batch>("/vocabulary/recommendations", source));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-teal-50 p-5">
        <h2 className="text-lg font-bold text-teal-900">
          Học cách diễn đạt từ chính bài vừa luyện
        </h2>
        <p className="mt-2 text-sm leading-7 text-teal-800">
          Gợi ý tập trung vào cụm từ tự nhiên, cách kết hợp từ và ý bạn muốn
          diễn đạt. Lưu những mục hữu ích rồi luyện nhớ và dùng lại trong câu
          mới.
        </p>
        {!batch?.items.length && (
          <Button className="mt-4" disabled={busy} onClick={generate}>
            {busy
              ? "Đang chọn từ theo ngữ cảnh..."
              : source.source_skill === "READING"
                ? "Gợi ý 5 cụm từ từ bài đọc"
                : "Tạo gợi ý từ bài của bạn"}
          </Button>
        )}
      </div>
      {error && <ErrorNotice message={error} />}
      {busy && (
        <Loading text="Đang chọn cụm từ, đối chiếu lỗi và chuẩn bị bài ôn..." />
      )}
      {!!batch?.batch_id &&
        groups.map((group) => {
          const items = batch.items.filter((i) =>
            group.types.includes(i.source_type),
          );
          return (
            <section key={group.title}>
              <h3 className="mb-4 font-bold">{group.title}</h3>
              {items.length ? (
                <div className="grid items-start gap-4 md:grid-cols-2">
                  {items.map((item) => (
                    <SuggestionCard
                      key={`${batch.batch_id}:${item.index}`}
                      item={item}
                      batchId={batch.batch_id!}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-stone-500">
                  Chưa có gợi ý có đủ bằng chứng trong nhóm này.
                </p>
              )}
            </section>
          );
        })}
      {source.source_skill !== "READING" && <ReuseChallenge source={source} />}
    </div>
  );
}
function ReuseChallenge({ source }: { source: Source }) {
  const router = useRouter();
  const [items, setItems] = useState<
    { id: string; phrase: string; challenge_vi: string }[]
  >([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const key = JSON.stringify(source);
  useEffect(() => {
    let active = true;
    post<{ items: typeof items }>("/vocabulary/reuse", JSON.parse(key))
      .then((r) => {
        if (active) setItems(r.items);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [key]);
  async function start(id: string) {
    setBusy(true);
    setError("");
    try {
      const review = await post<Review>(`/vocabulary/items/${id}/reviews`, {
        kind: "USE",
        client_request_id: crypto.randomUUID(),
      });
      router.push(`/vocabulary/review/${review.id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }
  if (!items.length) return error ? <ErrorNotice message={error} /> : null;
  return (
    <section className="panel space-y-4 p-6">
      <h3 className="font-bold">Dùng lại cụm từ đã học</h3>
      {items.map((item) => (
        <div
          key={item.id}
          className="flex flex-wrap items-center justify-between gap-3 text-sm"
        >
          <p>{item.challenge_vi}</p>
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => start(item.id)}
          >
            Thử đặt câu
          </Button>
        </div>
      ))}
      {error && <ErrorNotice message={error} />}
    </section>
  );
}
