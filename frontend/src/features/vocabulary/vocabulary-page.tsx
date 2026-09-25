"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Paywall } from "@/components/paywall";
import { api, post } from "@/services/api";
import { topicLabels as topics } from "./types";
import { LearningContent } from "./learning-card";
import { VocabularyProgressPanel } from "./progress";
import {
  issueLabels,
  masteryLabels,
  reviewKinds,
  sourceLink,
  type VocabularyItem,
  type VocabularyProgress,
  type Review,
  type ReviewKind,
} from "./types";

const sections = [
  ["DUE", "Từ cần học hôm nay"],
  ["NEW", "Từ mới"],
  ["LEARNING", "Đang học"],
  ["MASTERED", "Đã nhớ"],
  ["ERRORS", "Lỗi thường gặp"],
  ["HISTORY", "Lịch sử ôn"],
  ["ALL", "Tất cả"],
];
export function VocabularyPage() {
  return (
    <RequireAuth>
      <Library />
    </RequireAuth>
  );
}
function Library() {
  const router = useRouter();
  const { user } = useAuth();
  const free = user?.role !== "ADMIN" && user?.access?.tier !== "VIP";
  const [section, setSection] = useState("DUE");
  const [skill, setSkill] = useState("");
  const [topic, setTopic] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<{
    items: VocabularyItem[];
    total: number;
  } | null>(null);
  const [progress, setProgress] = useState<VocabularyProgress | null>(null);
  const [history, setHistory] = useState<{
    items: (Review & { phrase: string })[];
    total: number;
  } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    api<VocabularyProgress>("/vocabulary/progress")
      .then((r) => {
        if (active) setProgress(r);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [reload]);
  useEffect(() => {
    let active = true;
    if (section === "ERRORS") return;
    const timer = setTimeout(() => {
      setData(null);
      setHistory(null);
      setError("");
      if (section === "HISTORY")
        api<{ items: (Review & { phrase: string })[]; total: number }>(
          `/vocabulary/history?offset=${offset}&limit=20`,
        )
          .then((r) => {
            if (active) setHistory(r);
          })
          .catch((e) => {
            if (active) setError(e.message);
          });
      else {
        const params = new URLSearchParams({
          section,
          search,
          offset: String(offset),
          limit: "20",
        });
        if (skill) params.set("skill", skill);
        if (topic) params.set("topic", topic);
        api<{ items: VocabularyItem[]; total: number }>(
          `/vocabulary/items?${params}`,
        )
          .then((r) => {
            if (active) setData(r);
          })
          .catch((e) => {
            if (active) setError(e.message);
          });
      }
    }, 180);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [section, skill, topic, search, offset, reload]);
  async function review(item: VocabularyItem, kind: ReviewKind) {
    setBusy(true);
    setError("");
    try {
      const r = await post<Review>(`/vocabulary/items/${item.id}/reviews`, {
        kind,
        client_request_id: crypto.randomUUID(),
      });
      router.push(`/vocabulary/review?id=${r.id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }
  const total = data?.total ?? history?.total ?? 0;
  return (
    <div className="space-y-7">
      {free && <Paywall title="Mở Vocabulary Coach và ôn tập cá nhân" compact />}
      <div>
        <p className="eyebrow">Vocabulary Coach</p>
        <h1 className="mt-3 text-3xl font-bold">Từ đã gặp. Cụm từ sẽ dùng.</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-500">
          Lưu cách diễn đạt từ bài luyện, nhớ lại trong ngữ cảnh và dùng trong
          câu mới. Mỗi lượt ôn giúp bạn đưa vốn từ vào bài viết và bài nói tiếp
          theo.
        </p>
      </div>
      {progress && <VocabularyProgressPanel data={progress} />}
      <div
        className="flex gap-2 overflow-x-auto border-b border-stone-200 pb-3"
        aria-label="Nhóm từ vựng"
      >
        {sections.map(([key, label]) => (
          <Button
            key={key}
            variant={section === key ? "secondary" : "ghost"}
            size="sm"
            aria-pressed={section === key}
            onClick={() => {
              setSection(key);
              setOffset(0);
            }}
          >
            {label}
          </Button>
        ))}
      </div>
      {section !== "ERRORS" && section !== "HISTORY" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-xs font-semibold">
            Tìm cụm từ
            <input
              className="field mt-2"
              value={search}
              maxLength={100}
              onChange={(e) => {
                setSearch(e.target.value);
                setOffset(0);
              }}
              placeholder="Nhập cụm từ tiếng Anh"
            />
          </label>
          <label className="text-xs font-semibold">
            Nguồn
            <select
              className="field mt-2"
              value={skill}
              onChange={(e) => {
                setSkill(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">Mọi kỹ năng</option>
              {["WRITING", "SPEAKING", "READING"].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label className="text-xs font-semibold">
            Chủ đề
            <select
              className="field mt-2"
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">Mọi chủ đề</option>
              {Object.entries(topics)
                .filter(([key]) => key !== "random")
                .map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
            </select>
          </label>
        </div>
      )}
      {error && (
        <div>
          <ErrorNotice message={error} />
          <Button variant="outline" onClick={() => setReload((r) => r + 1)}>
            Thử tải lại
          </Button>
        </div>
      )}
      {section === "ERRORS" ? (
        <section className="panel space-y-4 p-6">
          <h2 className="font-bold">
            Mẫu lỗi từ bài Writing và Speaking đã chấm
          </h2>
          {progress?.recurring_errors
            .filter((e) => e.count >= 2)
            .map((e) => (
              <div
                key={`${e.issue_type}:${e.original}`}
                className="border-b border-stone-100 pb-4"
              >
                <p lang="en" className="font-semibold">
                  {e.original}
                </p>
                <p className="mt-1 text-xs text-stone-500">
                  {issueLabels[e.issue_type]} · Xuất hiện trong {e.count} bài
                </p>
              </div>
            ))}
          {!progress?.recurring_errors.some((e) => e.count >= 2) && (
            <p className="text-sm text-stone-500">
              Chưa ghi nhận mẫu lỗi xuất hiện ở ít nhất hai bài. Các lần chấm
              lại cùng một bài không được tính lặp.
            </p>
          )}
        </section>
      ) : section === "HISTORY" ? (
        history ? (
          <div className="panel divide-y divide-stone-100">
            {history.items.length ? (
              history.items.map((r) => (
                <Link
                  key={r.id}
                  href={`/vocabulary/review?id=${r.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 p-5 hover:bg-stone-50"
                >
                  <div>
                    <p lang="en" className="font-semibold">
                      {r.phrase}
                    </p>
                    <p className="mt-1 text-xs text-stone-500">
                      {reviewKinds[r.kind]} ·{" "}
                      {r.assessed_at
                        ? new Date(r.assessed_at).toLocaleString("vi-VN")
                        : "Chưa trả lời"}
                    </p>
                  </div>
                  <span className="text-sm">
                    {r.correct == null
                      ? "Chưa xác định"
                      : r.correct
                        ? "Đã nhớ đúng"
                        : "Cần ôn lại"}{" "}
                    →
                  </span>
                </Link>
              ))
            ) : (
              <p className="p-6 text-sm text-stone-500">
                Chưa có lượt ôn đã hoàn thành.
              </p>
            )}
          </div>
        ) : (
          !error && <Loading />
        )
      ) : data ? (
        data.items.length ? (
          <div className="grid items-start gap-5 lg:grid-cols-2">
            {data.items.map((item) => (
              <article key={item.id} className="panel p-6">
                <div className="mb-4 flex flex-wrap justify-between gap-2 text-xs">
                  <span className="rounded-full bg-teal-50 px-3 py-1 text-teal-800">
                    {masteryLabels[item.mastery_level]}
                  </span>
                  <Link
                    href={sourceLink(item)}
                    className="text-stone-500 underline"
                  >
                    {item.source_skill} ·{" "}
                    {topics[item.source_topic] || item.source_topic}
                  </Link>
                </div>
                <LearningContent
                  item={item}
                  original={item.user_original_text}
                  improved={item.improved_text}
                />
                <p className="mb-3 mt-5 text-xs text-stone-500">
                  {item.review_count} lượt ôn · Đúng {item.correct_review_count}{" "}
                  lượt
                  {item.next_review_at &&
                    ` · Hẹn ôn ${new Date(item.next_review_at).toLocaleDateString("vi-VN")}`}
                </p>
                <div className="flex flex-wrap gap-2">
                  {(Object.keys(reviewKinds) as ReviewKind[]).map((kind) => (
                    <Button
                      key={kind}
                      size="sm"
                      variant="outline"
                      disabled={
                        busy || free ||
                        (kind === "CORRECT" &&
                          (!item.user_original_text || !item.improved_text))
                      }
                      onClick={() => review(item, kind)}
                    >
                      {reviewKinds[kind]}
                    </Button>
                  ))}
                </div>
                {item.source_skill === "SPEAKING" && (
                  <Link
                    className="mt-4 inline-block text-xs font-semibold text-teal-700"
                    href={`/speaking/pronunciation?reference=${encodeURIComponent(item.phrase)}`}
                  >
                    Thu âm và luyện phát âm →
                  </Link>
                )}
              </article>
            ))}
          </div>
        ) : (
          <div className="panel p-8 text-center">
            <h2 className="font-bold">Chưa có từ trong nhóm này</h2>
            <p className="mt-3 text-sm text-stone-500">
              Mở “Từ vựng nên học” ở kết quả Writing/Speaking, hoặc chọn cụm từ
              trong bài Reading đã nộp để lưu.
            </p>
            <div className="mt-5 flex justify-center gap-4 text-sm text-teal-700">
              <Link href="/history">Bài luyện của bạn →</Link>
              <Link href="/reading/history">Bài đọc đã làm →</Link>
            </div>
          </div>
        )
      ) : (
        !error && <Loading />
      )}
      {total > 20 && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            disabled={!offset}
            onClick={() => setOffset((v) => Math.max(0, v - 20))}
          >
            Trang trước
          </Button>
          <p className="text-xs text-stone-500">
            {offset + 1}–{Math.min(offset + 20, total)} / {total}
          </p>
          <Button
            variant="outline"
            disabled={offset + 20 >= total}
            onClick={() => setOffset((v) => v + 20)}
          >
            Trang sau
          </Button>
        </div>
      )}
    </div>
  );
}
