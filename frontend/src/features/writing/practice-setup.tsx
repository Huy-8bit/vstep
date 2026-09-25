"use client";
import { LearningEntry } from "@/features/learning/integration";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Clock3,
  LoaderCircle,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Paywall } from "@/components/paywall";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { PracticeAssets } from "@/features/library/practice-assets";
import { post } from "@/services/api";
import { TEST_PROFILE } from "@/lib/test-profile";
import { topics, task1Types, task2Types } from "@/lib/constants";
import type { Exam, Question } from "@/types";

export function QuestionCard({ question }: { question: Question }) {
  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-2">
        <span className="rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-800">
          Task {question.task_type}
        </span>
        <span className="rounded-md bg-stone-100 px-2.5 py-1 text-xs text-stone-500">
          {topics[question.topic] || question.topic}
        </span>
        <span className="rounded-md bg-stone-100 px-2.5 py-1 text-xs text-stone-500">
          VSTEP.3–5 ·{" "}
          {question.source === "CUSTOM"
            ? "Đề của tôi"
            : question.source === "AI"
              ? "Đề AI"
              : "Đề mẫu"}
        </span>
      </div>
      <p lang="en" className="mb-4 text-sm italic text-stone-500">
        You should spend about {question.task_type === 1 ? 20 : 40} minutes on
        this task.
      </p>
      <p
        lang="en"
        className="whitespace-pre-wrap font-serif text-xl leading-relaxed text-stone-800"
      >
        {question.instruction}
      </p>
      <PracticeAssets ids={question.presentation?.practice_asset_ids} />
      {question.stimulus && (
        <blockquote
          lang="en"
          className="my-6 whitespace-pre-wrap rounded-xl border border-stone-200 bg-stone-50 p-5 font-serif text-lg leading-8 text-stone-700"
        >
          {question.stimulus}
        </blockquote>
      )}
      {question.response_instruction && (
        <p lang="en" className="mt-5 text-[15px] leading-7 text-stone-800">
          {question.response_instruction}
        </p>
      )}
      {(!question.stimulus ||
        question.presentation?.show_imported_requirements) &&
        question.requirements.length > 0 && (
          <ul
            lang="en"
            className="mt-5 list-disc space-y-3 pl-5 text-[15px] leading-7 text-stone-600"
          >
            {question.requirements.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        )}
      <p lang="en" className="mt-6 text-sm italic text-stone-500">
        Write at least {question.minimum_words} words.
      </p>
    </div>
  );
}

function Setup({ task }: { task: 1 | 2 }) {
  const router = useRouter();
  const { user } = useAuth();
  const free = user?.role !== "ADMIN" && user?.access?.tier !== "VIP";
  const [questionType, setQuestionType] = useState("random");
  const [topic, setTopic] = useState("random");
  const [source, setSource] = useState<"BANK" | "AI">("BANK");
  const [timed, setTimed] = useState(false);
  const [question, setQuestion] = useState<Question | null>(null);
  const [seen, setSeen] = useState<string[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  async function generate() {
    const result = await post<Question>("/questions/generate", {
      task,
      question_type: questionType,
      topic,
      source,
      test_profile: TEST_PROFILE,
      exclude_ids: seen.slice(-30),
    });
    setQuestion(result);
    setSeen((prev) => [...prev, result.id]);
    return result;
  }
  async function act(start: boolean) {
    setBusy(start ? "start" : "generate");
    setError("");
    try {
      const q = start && question ? question : await generate();
      if (start) {
        const exam = await post<Exam>("/exams", {
          mode: task === 1 ? "TASK1" : "TASK2",
          question_ids: [q.id],
          timed,
        });
        router.push(`/exam?id=${exam.id}`);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <>
      {free && (task === 2 || (user?.access?.trial_remaining.WRITING_TASK1 ?? 0) <= 0) ? <Paywall title={task === 2 ? "Writing Task 2 dành cho VIP" : "Bạn đã dùng lượt Writing Task 1 miễn phí"} /> : null}
      <p className="eyebrow">Luyện tập có chủ đích</p>
<LearningEntry skill="Writing" />
      <h1 className="mb-3 mt-3 text-3xl font-bold">
        Task {task} · {task === 1 ? "Viết thư & email" : "Viết bài luận"}
      </h1>
      <p className="mb-8 text-sm text-stone-500">
        {task === 1
          ? "Luyện đúng mục đích, đủ ý và phù hợp người nhận."
          : "Biến ý tưởng thành lập luận rõ ràng, mạch lạc."}
      </p>
      <div className="grid items-start gap-6 lg:grid-cols-[340px_1fr]">
        <div className="panel p-6">
          <h2 className="mb-6 font-bold">Thiết lập buổi luyện</h2>
          <div className="space-y-5">
            <div>
              <label
                htmlFor="source"
                className="mb-2 block text-sm font-semibold"
              >
                Nguồn đề
              </label>
              <select
                id="source"
                className="field"
                disabled={!!busy}
                value={source}
                onChange={(e) => {
                  setSource(e.target.value as "BANK" | "AI");
                  setQuestion(null);
                }}
              >
                <option value="BANK">Ngân hàng đề đã kiểm tra</option>
                {!free && <option value="AI">Sinh đề mới bằng AI</option>}
              </select>
            </div>
            <div>
              <label
                htmlFor="question-type"
                className="mb-2 block text-sm font-semibold"
              >
                Dạng đề
              </label>
              <select
                id="question-type"
                className="field"
                disabled={!!busy}
                value={questionType}
                onChange={(e) => {
                  setQuestionType(e.target.value);
                  setQuestion(null);
                }}
              >
                <option value="random">Ngẫu nhiên</option>
                {Object.entries(task === 1 ? task1Types : task2Types).map(
                  ([key, name]) => (
                    <option key={key} value={key}>
                      {name}
                    </option>
                  ),
                )}
              </select>
            </div>
            <div>
              <label
                htmlFor="topic"
                className="mb-2 block text-sm font-semibold"
              >
                Chủ đề
              </label>
              <select
                id="topic"
                className="field"
                disabled={!!busy}
                value={topic}
                onChange={(e) => {
                  setTopic(e.target.value);
                  setQuestion(null);
                }}
              >
                <option value="random">Ngẫu nhiên</option>
                {Object.entries(topics).map(([key, name]) => (
                  <option key={key} value={key}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
            <div className="rounded-xl bg-stone-50 p-4">
              <label className="flex items-center justify-between gap-3 text-sm font-medium">
                Bật đồng hồ luyện tập
                <input
                  type="checkbox"
                  checked={timed}
                  onChange={(e) => setTimed(e.target.checked)}
                  className="size-4 accent-teal-700"
                />
              </label>
              <p className="mt-2 text-xs leading-5 text-stone-500">
                {task === 1 ? 20 : 40} phút là thời gian luyện tập đề xuất,
                không phải giới hạn chính thức của từng Task.
              </p>
            </div>
          </div>
          <Button
            className="mt-6 w-full"
            disabled={!!busy || (free && (task === 2 || (user?.access?.trial_remaining.WRITING_TASK1 ?? 0) <= 0))}
            onClick={() => act(true)}
          >
            {busy === "start" ? (
              <LoaderCircle className="animate-spin" />
            ) : (
              <ArrowRight />
            )}
            Bắt đầu viết
          </Button>
        </div>
        <div className="panel min-h-96 p-6 sm:p-8">
          <div className="mb-7 flex items-center justify-between gap-4">
            <h2 className="font-bold">Đề luyện tập</h2>
            <Button
              variant="outline"
              size="sm"
              disabled={!!busy || (free && (task === 2 || (user?.access?.trial_remaining.WRITING_TASK1 ?? 0) <= 0))}
              onClick={() => act(false)}
            >
              {busy === "generate" ? (
                <LoaderCircle className="animate-spin" />
              ) : source === "AI" ? (
                <Sparkles />
              ) : (
                <RefreshCw />
              )}
              {source === "AI" ? "Sinh đề mới" : "Đề ngẫu nhiên"}
            </Button>
          </div>
          {error && <ErrorNotice message={error} />}
          {question ? (
            <QuestionCard question={question} />
          ) : (
            <div className="flex min-h-64 flex-col items-center justify-center text-center">
              <div className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                <Sparkles size={24} />
              </div>
              <h3 className="font-semibold">Một đề bài mới đang chờ bạn</h3>
              <p className="mt-3 max-w-sm text-sm leading-6 text-stone-500">
                Chọn dạng đề, chủ đề rồi lấy đề để xem trước. Hoặc bắt đầu ngay
                với một đề ngẫu nhiên.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
export function PracticeSetup({ task }: { task: 1 | 2 }) {
  return (
    <RequireAuth>
      <Setup task={task} />
    </RequireAuth>
  );
}
export function FullTestStart() {
  const router = useRouter();
  const { user } = useAuth();
  const free = user?.role !== "ADMIN" && user?.access?.tier !== "VIP";
  const [source, setSource] = useState("BANK");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function start() {
    setBusy(true);
    setError("");
    try {
      const ids: string[] = [];
      if (source === "AI")
        for (const task of [1, 2]) {
          const q = await post<Question>("/questions/generate", {
            task,
            source: "AI",
          });
          ids.push(q.id);
        }
      const exam = await post<Exam>("/exams", {
        mode: "FULL_TEST",
        timed: true,
        question_ids: ids,
      });
      router.push(`/exam?id=${exam.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section id="full-test" className="panel mt-8 scroll-mt-32 p-6 sm:p-8">
      {free && <div className="mb-5"><Paywall title="Thi thử Writing đầy đủ dành cho VIP" compact /></div>}
      <div className="flex flex-wrap items-center justify-between gap-6">
        <div>
          <p className="eyebrow mb-3">Sẵn sàng thử sức?</p>
          <h2 className="text-xl font-bold">Một phiên Writing hoàn chỉnh</h2>
          <p className="mt-3 max-w-xl text-sm leading-7 text-stone-500">
            60 phút cho cả hai Task. Bạn có thể chuyển qua lại và phân bổ thời
            gian theo cách của mình. Phản hồi AI xuất hiện sau khi nộp bài.
          </p>
        </div>
        <div className="flex min-w-56 flex-col gap-3">
          <label
            htmlFor="full-source"
            className="text-xs font-semibold text-stone-500"
          >
            Nguồn đề thi
          </label>
          <select
            id="full-source"
            className="field"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            disabled={busy}
          >
            <option value="BANK">Ngân hàng đề đã kiểm tra</option>
            {!free && <option value="AI">Sinh cả hai đề bằng AI</option>}
          </select>
          <Button disabled={busy || free} onClick={start}>
            {busy ? <LoaderCircle className="animate-spin" /> : <Clock3 />}
            {busy ? "Đang chuẩn bị đề..." : "Bắt đầu thi thử"}
          </Button>
        </div>
      </div>
      {error && <ErrorNotice message={error} />}
    </section>
  );
}
