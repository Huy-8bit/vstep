"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api, post } from "@/services/api";
import { masteryLabels, reviewKinds, type Review } from "./types";

export function VocabularyReview({ id }: { id: string }) {
  return (
    <RequireAuth>
      <Exercise key={id} id={id} />
    </RequireAuth>
  );
}
function Exercise({ id }: { id: string }) {
  const { user } = useAuth();
  const [review, setReview] = useState<Review | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const key = `vstep-vocabulary-review:${user?.id}:${id}`;
  const load = useCallback(
    () =>
      api<Review>(`/vocabulary/reviews/${id}`)
        .then((r) => {
          setError("");
          setReview(r);
          let draft = "";
          try {
            draft = localStorage.getItem(key) || "";
          } catch {}
          setAnswer(r.answer || draft);
        })
        .catch((e) => setError(e.message)),
    [id, key],
  );
  useEffect(() => {
    void load();
  }, [load]);
  function change(value: string) {
    setAnswer(value);
    try {
      localStorage.setItem(key, value);
    } catch {}
  }
  async function submit() {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    try {
      setReview(
        await post<Review>(`/vocabulary/reviews/${id}/answer`, { answer }),
      );
      try {
        localStorage.removeItem(key);
      } catch {}
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      sending.current = false;
    }
  }
  if (!review)
    return error ? (
      <>
        <ErrorNotice message={error} />
        <Button onClick={load}>Thử tải lại</Button>
      </>
    ) : (
      <Loading />
    );
  const feedback = review.feedback;
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Link href="/vocabulary" className="text-sm text-teal-700">
        ← Sổ từ vựng
      </Link>
      <div>
        <p className="eyebrow">Ôn chủ động · {reviewKinds[review.kind]}</p>
        <h1 className="mt-3 text-2xl font-bold">
          {review.prompt.instruction_vi}
        </h1>
      </div>
      <section className="panel space-y-5 p-6 sm:p-8">
        <p className="text-sm leading-7 text-stone-500">
          {review.prompt.context}
        </p>
        <p
          lang={review.kind === "RECALL" ? "vi" : "en"}
          className="whitespace-pre-wrap font-serif text-xl leading-relaxed"
        >
          {review.prompt.text}
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
          className="space-y-5"
        >
          {review.prompt.options.length ? (
            <fieldset
              disabled={busy || !!review.assessed_at}
              className="space-y-3"
            >
              <legend className="mb-3 text-sm font-semibold">
                Chọn một cách diễn đạt
              </legend>
              {review.prompt.options.map((option) => (
                <label
                  key={option}
                  className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 ${answer === option ? "border-teal-700 bg-teal-50" : "border-stone-200"}`}
                >
                  <input
                    type="radio"
                    name="answer"
                    checked={answer === option}
                    onChange={() => change(option)}
                    value={option}
                    className="accent-teal-700"
                  />
                  <span lang="en">{option}</span>
                </label>
              ))}
            </fieldset>
          ) : (
            <label className="block text-sm font-semibold">
              Câu trả lời của bạn
              <textarea
                lang="en"
                className="field mt-2 min-h-28 font-normal"
                maxLength={1200}
                value={answer}
                onChange={(e) => change(e.target.value)}
                disabled={busy || !!review.assessed_at}
                autoComplete="off"
                spellCheck={false}
                placeholder={
                  review.kind === "USE"
                    ? "Write a new sentence..."
                    : "Type the expression you remember..."
                }
              />
            </label>
          )}
          {!review.assessed_at && (
            <Button type="submit" disabled={!answer.trim() || busy}>
              {busy ? "Đang đánh giá..." : "Kiểm tra câu trả lời"}
            </Button>
          )}
        </form>
        {error && <ErrorNotice message={error} />}
      </section>
      {feedback && (
        <section
          className={`space-y-4 rounded-2xl border p-6 ${review.correct ? "border-teal-200 bg-teal-50" : "border-amber-200 bg-amber-50"}`}
        >
          <h2 className="text-lg font-bold">
            {review.correct == null
              ? "Chưa đủ độ tin cậy để đánh giá"
              : review.correct
                ? "Bạn đã dùng đúng"
                : "Cùng xem lại cách diễn đạt"}
          </h2>
          <p className="text-sm leading-7">{feedback.explanation_vi}</p>
          <p lang="en" className="font-semibold">
            {feedback.suggested_answer}
          </p>
          <p lang="en" className="text-sm italic leading-7">
            {feedback.example_sentence}
          </p>
          <p className="text-xs leading-6 text-stone-600">
            {masteryLabels[feedback.mastery_level]}
            {feedback.next_review_at &&
              ` · Hẹn ôn ${new Date(feedback.next_review_at).toLocaleDateString("vi-VN")}`}
            {!feedback.progression_applied &&
              " · Mức ghi nhớ được giữ nguyên ở lượt này."}
          </p>
          {review.kind === "USE" && (
            <p className="text-xs text-stone-500">
              Phản hồi luyện tập do AI ước tính; không dùng làm điểm VSTEP.
            </p>
          )}
          <Button asChild>
            <Link href="/vocabulary">Tiếp tục ôn từ</Link>
          </Button>
        </section>
      )}
    </div>
  );
}
