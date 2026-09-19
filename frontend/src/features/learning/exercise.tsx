"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CheckCircle2, LoaderCircle, Mic } from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { post } from "@/services/api";
import { LearningHeader, LoadError, useLearning } from "./shared";
import { kinds, type Exercise } from "./types";
export function LearningExercise({ id }: { id: string }) {
  return (
    <RequireAuth>
      <ExerciseView id={id} />
    </RequireAuth>
  );
}
function ExerciseView({ id }: { id: string }) {
  const { data, error, reload, setData } = useLearning<Exercise>(
    `/exercises/${id}`,
  );
  const [index, setIndex] = useState(0);
  if (error) return <LoadError message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <LearningHeader
        title={data.title}
        description="Luyện từng câu, đọc phản hồi rồi áp dụng trong một tình huống mới."
      />
      <Link
        href={`/learning/weaknesses/${data.weakness_id}`}
        className="text-sm text-teal-800 underline"
      >
        ← Quay lại bài học và bằng chứng
      </Link>
      <div className="panel p-5">
        <div className="flex flex-wrap justify-between gap-3 text-sm">
          <span>
            Đã trả lời {data.answered_count}/{data.items.length} câu
          </span>
          <span>{data.correct_count} câu có bằng chứng đúng</span>
        </div>
        <div className="mt-3 h-2 rounded-full bg-stone-100">
          <div
            className="h-full rounded-full bg-teal-600 transition-all"
            style={{
              width: `${data.items.length ? (data.answered_count / data.items.length) * 100 : 0}%`,
            }}
          />
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {data.items.map((item, i) => (
            <button
              aria-label={`Câu ${i + 1}${item.result ? ", đã làm" : ""}`}
              aria-pressed={index === i}
              className={`size-9 rounded-lg text-sm ${index === i ? "bg-teal-800 text-white" : item.result ? "bg-teal-50 text-teal-900" : "bg-stone-100"}`}
              onClick={() => setIndex(i)}
              key={i}
            >
              {i + 1}
            </button>
          ))}
        </div>
      </div>
      {data.items[index] && (
        <ExerciseItem
          key={`${id}:${index}`}
          exercise={data}
          index={index}
          onResult={setData}
        />
      )}
      {index < data.items.length - 1 && (
        <Button
          variant="outline"
          className="w-full"
          onClick={() => setIndex((i) => i + 1)}
        >
          Câu tiếp theo →
        </Button>
      )}
      {data.completed_at && (
        <div className="rounded-2xl bg-teal-50 p-6">
          <h2 className="flex items-center gap-2 font-semibold">
            <CheckCircle2 size={19} />
            Đã hoàn thành lượt luyện
          </h2>
          <p className="mt-3 text-sm leading-7 text-teal-900">
            Tiếp tục dùng nội dung này trong một bài mới. Một lượt luyện tốt là
            bước tiến; việc thành thạo cần được chứng minh qua nhiều ngữ cảnh.
          </p>
          <Button asChild className="mt-4">
            <Link href={`/learning/weaknesses/${data.weakness_id}`}>
              Xem tiến bộ và luyện tiếp
            </Link>
          </Button>
        </div>
      )}
    </div>
  );
}
function ExerciseItem({
  exercise,
  index,
  onResult,
}: {
  exercise: Exercise;
  index: number;
  onResult: (value: Exercise) => void;
}) {
  const item = exercise.items[index];
  const [answer, setAnswer] = useState(item.result?.answer || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const started = useRef<number | null>(null);
  const requestId = useRef<string | null>(null);
  const router = useRouter();
  function interact(value: string) {
    started.current ??= Date.now();
    setAnswer(value);
  }
  async function submit() {
    setBusy(true);
    setError("");
    try {
      const result = await post<Exercise>(
        `/learning/exercises/${exercise.id}/answer`,
        {
          item_index: index,
          answer,
          duration_seconds: Math.min(
            900,
            Math.round((Date.now() - (started.current ?? Date.now())) / 1000),
          ),
        },
      );
      onResult(result);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function record() {
    setBusy(true);
    setError("");
    requestId.current ??= crypto.randomUUID();
    try {
      const result = await post<{ url: string }>(
        `/learning/weaknesses/${exercise.weakness_id}/targeted-practice`,
        {
          client_request_id: requestId.current,
          skill: "SPEAKING",
          part:
            item.kind === "PART2_COMPARISON"
              ? 2
              : item.kind === "SHORT_ANSWER"
                ? 1
                : 3,
          exercise_id: exercise.id,
          item_index: index,
        },
      );
      router.push(result.url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel p-6 sm:p-8">
      <p className="eyebrow">
        CÂU {index + 1} · {kinds[item.kind]}
      </p>
      <h2 className="mt-4 text-lg font-semibold">{item.instruction_vi}</h2>
      {item.passage && (
        <div
          lang="en"
          className="mt-5 whitespace-pre-wrap rounded-xl bg-stone-50 p-5 font-serif text-lg leading-9"
        >
          {item.passage}
        </div>
      )}
      <p lang="en" className="my-6 whitespace-pre-wrap text-lg leading-9">
        {item.text}
      </p>
      {error && <ErrorNotice message={error} />}
      {item.evaluation === "RECORDING" ? (
        <div>
          <p className="mb-4 text-sm text-stone-500">
            {item.seconds ? `Mục tiêu: ${item.seconds} giây. ` : ""}Mở phần
            Speaking để ghi âm và nhận phản hồi từ bài nói thật.
          </p>
          {item.target_words.length > 0 && (
            <p lang="en" className="mb-4 text-sm font-medium">
              {item.target_words.join(" · ")}
            </p>
          )}
          <Button disabled={busy} onClick={record}>
            {busy ? <LoaderCircle className="animate-spin" /> : <Mic />}Mở bài
            luyện có ghi âm
          </Button>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
          className="space-y-4"
        >
          {item.options.length ? (
            <fieldset disabled={busy || !!item.result}>
              <legend className="sr-only">Chọn đáp án</legend>
              <div className="space-y-3">
                {item.options.map((option) => (
                  <label
                    key={option}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 text-sm leading-7 ${answer === option ? "border-teal-700 bg-teal-50" : "border-stone-200"}`}
                  >
                    <input
                      type="radio"
                      name="answer"
                      value={option}
                      checked={answer === option}
                      onChange={() => interact(option)}
                      className="mt-2"
                    />
                    <span lang="en">{option}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ) : (
            <label className="block text-sm">
              Câu trả lời của bạn
              <textarea
                className="field mt-2 min-h-36 w-full"
                lang="en"
                maxLength={6000}
                value={answer}
                disabled={busy || !!item.result}
                onChange={(e) => interact(e.target.value)}
                placeholder="Write your answer here…"
              />
            </label>
          )}
          {!item.result && (
            <Button disabled={busy || !answer.trim()} type="submit">
              {busy && <LoaderCircle className="animate-spin" />}Kiểm tra câu
              trả lời
            </Button>
          )}
        </form>
      )}
      {item.result && (
        <div
          role="status"
          className={`mt-6 rounded-xl p-5 ${item.result.correct === true ? "bg-teal-50" : "bg-amber-50"}`}
        >
          <h3 className="font-semibold">
            {item.result.correct === true
              ? "Bạn đã dùng đúng nội dung đang luyện"
              : item.result.correct === false
                ? "Xem lại cách dùng này"
                : "Chưa đủ chắc chắn để kết luận"}
          </h3>
          <p className="mt-3 text-sm leading-7">
            {item.result.feedback.explanation_vi}
          </p>
          {item.result.feedback.suggested_answer && (
            <p
              lang="en"
              className="mt-3 whitespace-pre-wrap text-sm leading-7 text-stone-600"
            >
              {item.result.feedback.suggested_answer}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
