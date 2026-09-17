"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Circle, Search, XCircle } from "lucide-react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api, post } from "@/services/api";
import { SuggestionCard } from "@/features/vocabulary/learning-card";
import { VocabularyRecommendations } from "@/features/vocabulary/recommendations";
import type { Batch } from "@/features/vocabulary/types";
import { ReadingPlacement } from "./reading-placement";
import { ReadingPassage } from "./reading-passage";
import { draftKey, type Draft } from "./use-reading-autosave";
import {
  disclaimer,
  duration,
  modes,
  options,
  questionTypes,
  type ReadingResult as Result,
} from "./types";
export function ReadingResult({ id }: { id: string }) {
  return (
    <RequireAuth>
      <ResultView id={id} />
    </RequireAuth>
  );
}
function ResultView({ id }: { id: string }) {
  const { user } = useAuth();
  const [data, setData] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState("");
  const [mobile, setMobile] = useState("questions");
  const [highlight, setHighlight] = useState<string | null>(null);
  const [jump, setJump] = useState(0);
  const [unsynced, setUnsynced] = useState<
    { number: number; answer: string | null }[]
  >([]);
  const [term, setTerm] = useState("");
  const [paragraph, setParagraph] = useState("p1");
  const [vocab, setVocab] = useState<Batch | null>(null);
  const [vocabError, setVocabError] = useState("");
  const [vocabBusy, setVocabBusy] = useState(false);
  const vocabRequest = useRef(0);
  const load = useCallback(async () => {
    setError("");
    try {
      const result = await api<Result>(`/reading/results/${id}`);
      setData(result);
      setSelected(result.review[0]?.id || "");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (!data || !user) return;
    try {
      const drafts: Record<string, Draft> = JSON.parse(
        localStorage.getItem(draftKey(user.id, id)) || "{}",
      );
      setUnsynced(
        data.review
          .filter(
            (q) =>
              drafts[q.id]?.dirty &&
              drafts[q.id].selected_answer !== q.selected_answer,
          )
          .map((q) => ({
            number: q.question_number,
            answer: drafts[q.id].selected_answer,
          })),
      );
    } catch {
      /* Result is authoritative even without local storage. */
    }
  }, [data, user, id]);
  const filtered =
    data?.review.filter(
      (q) =>
        filter === "all" ||
        (filter === "correct"
          ? q.is_correct === true
          : filter === "incorrect"
            ? q.is_correct === false
            : q.selected_answer === null),
    ) || [];
  const question = filtered.find((q) => q.id === selected) || filtered[0];
  const passage = data?.session.passages.find(
    (p) => p.id === question?.passage_id,
  );
  useEffect(() => {
    setTerm("");
    setParagraph("p1");
    setVocab(null);
    setVocabError("");
    setHighlight(null);
  }, [passage?.id]);
  useEffect(() => {
    vocabRequest.current += 1;
    setVocab(null);
    setVocabError("");
    setVocabBusy(false);
  }, [passage?.id, term, paragraph]);
  async function lookup() {
    if (!passage) return;
    const request = ++vocabRequest.current;
    setVocabBusy(true);
    setVocabError("");
    try {
      const response = await post<Batch>("/vocabulary/recommendations", {
        source_skill: "READING",
        source_attempt_id: id,
        passage_id: passage.id,
        paragraph_id: paragraph,
        term,
      });
      if (request === vocabRequest.current) setVocab(response);
    } catch (e) {
      if (request === vocabRequest.current) setVocabError((e as Error).message);
    } finally {
      if (request === vocabRequest.current) setVocabBusy(false);
    }
  }
  if (!data)
    return error ? (
      <>
        <ErrorNotice message={error} />
        <div className="flex gap-3">
          <Button onClick={load}>Thử lại</Button>
          <Button asChild variant="outline">
            <Link href={`/reading/exam/${id}`}>Quay lại phiên</Link>
          </Button>
        </div>
      </>
    ) : (
      <Loading text="Đang mở kết quả Reading..." />
    );
  const { result, session } = data;
  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">VSTEP.3–5 · {modes[session.mode].title}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Kết quả Reading
          </h1>
          <p className="mt-2 text-xs text-stone-500">
            {new Date(session.started_at).toLocaleString("vi-VN")}
            {session.status === "EXPIRED" ? " · Đã nộp khi hết giờ" : ""}
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href={`/reading?mode=${session.mode}`}>Luyện bài khác →</Link>
        </Button>
      </div>
      <section className="grid gap-5 rounded-2xl bg-teal-900 p-7 text-white sm:grid-cols-4">
        <div>
          <p className="text-xs text-teal-100">Câu trả lời đúng</p>
          <p className="mt-3 text-4xl font-bold">
            {result.correct_count}
            <span className="text-xl font-normal text-teal-200">
              {" "}
              / {session.question_count}
            </span>
          </p>
        </div>
        <div>
          <p className="text-xs text-teal-100">Tỷ lệ đúng</p>
          <p className="mt-3 text-4xl font-bold">{result.accuracy}%</p>
        </div>
        <div>
          <p className="text-xs text-teal-100">Điểm luyện tập tham khảo</p>
          <p className="mt-3 text-4xl font-bold">
            {result.score.toFixed(2)}
            <span className="text-xl font-normal text-teal-200"> / 10</span>
          </p>
        </div>
        <div>
          <p className="text-xs text-teal-100">Thời gian làm bài</p>
          <p className="mt-3 text-4xl font-bold tabular-nums">
            {duration(result.duration_seconds)}
          </p>
        </div>
      </section>
      {unsynced.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-900">
          <p className="font-semibold">
            Có {unsynced.length} lựa chọn trên thiết bị chưa được chốt vào kết
            quả.
          </p>
          <p className="mt-2">
            Máy chủ đã khóa bài khi nộp/hết giờ. Bản dự phòng còn lại:{" "}
            {unsynced
              .map((q) => `câu ${q.number}: ${q.answer || "trống"}`)
              .join("; ")}
            . Kết quả dùng đáp án đã nhận đúng hạn.
          </p>
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {session.passages.map((p, i) => {
          const row = result.passage_breakdown.find((b) => b.key === p.id)!;
          return (
            <button
              key={p.id}
              onClick={() => {
                setFilter("all");
                setSelected(data.review.find((q) => q.passage_id === p.id)!.id);
              }}
              className="panel p-5 text-left hover:border-teal-400"
            >
              <p className="eyebrow">Passage {i + 1}</p>
              <p className="mt-2 text-sm font-semibold">{p.title}</p>
              <p className="mt-3 text-xl font-bold text-teal-800">
                {row.correct} / {row.total}
              </p>
              <p className="mt-2 text-xs text-stone-400">
                Đang xem câu hỏi: ~{duration(row.time_spent_seconds)}
              </p>
            </button>
          );
        })}
      </div>
      <section className="panel p-6">
        <h2 className="mb-4 text-lg font-bold">Nhịp đọc của bạn</h2>
        <div className="grid gap-5 md:grid-cols-3">
          {result.strategy_feedback.map((item, i) => (
            <div key={i}>
              <h3 className="text-sm font-semibold">
                {item.question_type
                  ? `${item.kind === "strength" ? "Làm tốt hơn ở" : "Ưu tiên luyện"} ${questionTypes[item.question_type]}`
                  : item.title_vi}
              </h3>
              <p className="mt-2 text-sm leading-6 text-stone-500">
                {item.explanation_vi}
              </p>
              {item.question_type && (
                <Link
                  className="mt-3 inline-block text-xs font-semibold text-teal-800"
                  href={`/reading?mode=QUESTION_TYPE_PRACTICE&type=${item.question_type}`}
                >
                  Luyện dạng này →
                </Link>
              )}
            </div>
          ))}
        </div>
      </section>
      <section className="panel overflow-hidden">
        <div className="border-b border-stone-100 p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-lg font-bold">Xem lại từng câu</h2>
            <label className="text-xs font-semibold">
              Lọc kết quả
              <select
                className="field mt-2 py-2"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="all">Tất cả ({session.question_count})</option>
                <option value="correct">Đúng ({result.correct_count})</option>
                <option value="incorrect">
                  Sai ({result.incorrect_count})
                </option>
                <option value="unanswered">
                  Bỏ trống ({result.unanswered_count})
                </option>
              </select>
            </label>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {filtered.map((q) => (
              <button
                key={q.id}
                aria-label={`Câu ${q.question_number}: ${q.is_correct === true ? "đúng" : q.is_correct === false ? "sai" : "bỏ trống"}`}
                onClick={() => {
                  setSelected(q.id);
                  setHighlight(null);
                  setMobile("questions");
                }}
                className={`flex h-9 min-w-12 items-center justify-center gap-1 rounded-lg border px-2 text-xs font-semibold ${question?.id === q.id ? "ring-2 ring-teal-700 ring-offset-1" : ""} ${q.is_correct === true ? "border-teal-200 bg-teal-50 text-teal-800" : q.is_correct === false ? "border-red-200 bg-red-50 text-red-800" : "border-stone-200 bg-stone-50 text-stone-500"}`}
              >
                {q.is_correct === true ? (
                  <CheckCircle2 size={12} />
                ) : q.is_correct === false ? (
                  <XCircle size={12} />
                ) : (
                  <Circle size={12} />
                )}
                {q.question_number}
              </button>
            ))}
          </div>
        </div>
        {question && passage ? (
          <>
            <div className="flex gap-2 p-3 lg:hidden">
              {[
                ["passage", "Bài đọc"],
                ["questions", "Giải thích"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setMobile(key)}
                  className={`flex-1 rounded-lg py-2 text-sm ${mobile === key ? "bg-teal-100 text-teal-900" : "bg-stone-50"}`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="grid h-[75dvh] min-h-[450px] max-h-[950px] lg:grid-cols-2">
              <div
                className={`min-h-0 lg:block ${mobile === "passage" ? "block" : "hidden"}`}
              >
                <ReadingPassage
                  key={`${passage.id}:${jump}`}
                  passage={passage}
                  highlight={highlight}
                  onTerm={(word, p) => {
                    setTerm(word);
                    setParagraph(p);
                    setVocab(null);
                    setMobile("questions");
                  }}
                />
              </div>
              <div
                className={`min-h-0 overflow-y-auto border-stone-200 bg-stone-50/50 p-5 sm:p-7 lg:block lg:border-l ${mobile === "questions" ? "block" : "hidden"}`}
              >
                <p className="eyebrow">
                  Câu {question.question_number} ·{" "}
                  {questionTypes[question.question_type]}
                </p>
                <h3 className="mt-3 text-lg font-semibold leading-8">
                  {question.question_text}
                </h3>
                <ReadingPlacement question={question} passage={passage} />
                <div className="my-5 flex flex-wrap gap-3 text-sm">
                  <span className="rounded-lg border border-stone-200 bg-white px-3 py-2">
                    Bạn chọn:{" "}
                    <strong>
                      {question.selected_answer || "Chưa trả lời"}
                    </strong>
                  </span>
                  <span className="rounded-lg bg-teal-100 px-3 py-2 text-teal-900">
                    Đáp án đúng: <strong>{question.correct_answer}</strong>
                  </span>
                  <span
                    className={`rounded-lg px-3 py-2 font-semibold ${question.is_correct === true ? "text-teal-800" : question.is_correct === false ? "text-red-700" : "text-stone-500"}`}
                  >
                    {question.is_correct === true
                      ? "✓ Chính xác"
                      : question.is_correct === false
                        ? "✕ Chưa đúng"
                        : "○ Bỏ trống"}
                  </span>
                </div>
                <p className="mb-5 text-sm leading-7 text-stone-600">
                  {question.explanation_vi}
                </p>
                <div className="space-y-3">
                  {options.map((letter) => (
                    <article
                      key={letter}
                      className={`rounded-xl border p-4 ${letter === question.correct_answer ? "border-teal-200 bg-teal-50" : "border-stone-200 bg-white"}`}
                    >
                      <p className="text-sm font-semibold leading-6">
                        {letter}. {question.options[letter]}{" "}
                        <span
                          className={`ml-1 text-xs ${letter === question.correct_answer ? "text-teal-700" : "text-stone-400"}`}
                        >
                          ({letter === question.correct_answer ? "Đúng" : "Sai"}
                          )
                        </span>
                      </p>
                      <p className="mt-2 text-sm leading-7 text-stone-500">
                        {question.option_explanations[letter].explanation_vi}
                      </p>
                    </article>
                  ))}
                </div>
                <section className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-5">
                  <h4 className="text-sm font-bold">
                    Bằng chứng trong bài · Paragraph{" "}
                    {question.evidence.paragraph_id.slice(1)}
                  </h4>
                  <blockquote className="my-3 text-sm leading-7 text-stone-600">
                    “{question.evidence.quote}”
                  </blockquote>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setHighlight(question.evidence.paragraph_id);
                      setJump((j) => j + 1);
                      setMobile("passage");
                    }}
                  >
                    Xem trong bài →
                  </Button>
                </section>
                <section className="mt-6 rounded-xl border border-stone-200 bg-white p-5">
                  <h4 className="font-bold">Giải thích từ vựng</h4>
                  <p className="mt-2 text-xs leading-6 text-stone-500">
                    Chạm một từ hoặc bôi đen cụm từ trong bài. Bạn cũng có thể
                    nhập từ có trong đoạn đang chọn.
                  </p>
                  <label className="mt-4 block text-xs font-semibold">
                    Từ / cụm từ
                    <input
                      className="field mt-2"
                      value={term}
                      maxLength={100}
                      onChange={(e) => setTerm(e.target.value)}
                      placeholder="Ví dụ: a word from the passage"
                    />
                  </label>
                  <label className="mt-3 block text-xs font-semibold">
                    Đoạn văn
                    <select
                      className="field mt-2"
                      value={paragraph}
                      onChange={(e) => setParagraph(e.target.value)}
                    >
                      {passage.paragraphs.map((p, i) => (
                        <option key={p.id} value={p.id}>
                          Paragraph {i + 1}
                        </option>
                      ))}
                    </select>
                  </label>
                  <Button
                    className="mt-4"
                    size="sm"
                    disabled={!term.trim() || vocabBusy}
                    onClick={lookup}
                  >
                    <Search />
                    {vocabBusy
                      ? "Đang giải thích..."
                      : "Giải thích trong ngữ cảnh"}
                  </Button>
                  {vocabError && <ErrorNotice message={vocabError} />}
                  {vocab?.batch_id && (
                    <div className="mt-5">
                      {vocab.items.map((item) => (
                        <SuggestionCard
                          key={`${vocab.batch_id}:${item.index}`}
                          batchId={vocab.batch_id!}
                          item={item}
                        />
                      ))}
                    </div>
                  )}
                </section>
              </div>
            </div>
          </>
        ) : (
          <p className="p-8 text-center text-sm text-stone-500">
            Không có câu hỏi thuộc nhóm này.
          </p>
        )}
      </section>
      {passage && (
        <VocabularyRecommendations
          key={passage.id}
          source={{
            source_skill: "READING",
            source_attempt_id: id,
            passage_id: passage.id,
          }}
        />
      )}
      <p className="text-xs leading-6 text-stone-500">
        {disclaimer} Thời gian xem từng câu được ước lượng từ lúc cửa sổ đang
        hoạt động, không phải phép đo chính xác thời gian suy nghĩ.
      </p>
    </div>
  );
}
