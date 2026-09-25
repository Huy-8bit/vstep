"use client";
import { AttemptLearningSignals } from "@/features/learning/integration";
import {
  WritingEvidencePanel,
  WritingGradingHistory,
} from "./writing-evidence";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Download,
  LoaderCircle,
  Sparkles,
  Target,
} from "lucide-react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { VocabularyRecommendations } from "@/features/vocabulary/recommendations";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { QuestionCard } from "@/features/writing/practice-setup";
import { Paywall } from "@/components/paywall";
import { LibraryOrigin } from "@/features/library/practice-link";
import { api, post } from "@/services/api";
import { categories, criteria, topics } from "@/lib/constants";
import { cn, DISCLAIMER, formatDate, score } from "@/lib/utils";
import { draftKey } from "@/hooks/use-autosave";
import type {
  AttemptDetail,
  Grading,
  Improvement,
  WritingError,
} from "@/types";

function ImprovementList({ items }: { items: Improvement[] }) {
  return (
    <div className="space-y-4">
      {items.map((item, i) => (
        <div key={i} className="rounded-xl border border-stone-200 p-5">
          <h4 className="text-sm font-semibold">{item.title_vi}</h4>
          <p className="mt-2 text-sm leading-7 text-stone-600">
            {item.explanation_vi}
          </p>
          {item.example && (
            <p
              lang="en"
              className="mt-3 rounded-lg bg-stone-50 p-3 text-sm italic leading-6 text-teal-800"
            >
              {item.example}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
function ErrorList({ errors }: { errors: WritingError[] }) {
  return errors.length ? (
    <div className="space-y-4">
      {errors.map((error, i) => (
        <div
          key={error.id || i}
          className="rounded-xl border border-stone-200 p-5"
        >
          <div className="mb-4 flex items-center gap-2">
            <span className="rounded bg-stone-100 px-2 py-1 text-xs">
              {categories[error.category] || "Diễn đạt"}
            </span>
            <span
              className={cn(
                "text-xs",
                error.severity === "minor"
                  ? "text-stone-400"
                  : "text-amber-700",
              )}
            >
              {{
                minor: "Lỗi nhẹ",
                major: "Cần chú ý",
                critical: "Ảnh hưởng ý nghĩa",
              }[error.severity] || error.severity}
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-red-50 p-3">
              <p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-red-700">
                Câu / Cụm từ gốc
              </p>
              <p lang="en" className="text-sm leading-6 text-stone-700">
                {error.original || "Chưa có nội dung"}
              </p>
            </div>
            <div className="rounded-lg bg-teal-50 p-3">
              <p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-teal-700">
                Đề xuất sửa
              </p>
              <p lang="en" className="text-sm leading-6 text-teal-900">
                {error.corrected}
              </p>
            </div>
          </div>
          <p className="mt-4 text-sm leading-7 text-stone-500">
            {error.explanation_vi}
          </p>
        </div>
      ))}
    </div>
  ) : (
    <p className="rounded-xl bg-teal-50 p-6 text-sm text-teal-800">
      AI không ghi nhận lỗi thuộc nhóm này trong bài viết.
    </p>
  );
}

function Feedback({
  grading,
  answer,
  attemptId,
  ready,
  onUpdate,
}: {
  grading: Grading;
  answer: string;
  attemptId: string;
  ready: string[];
  onUpdate: () => Promise<unknown>;
}) {
  const [showAll, setShowAll] = useState(false);
  const [busy, setBusy] = useState("");
  const [optionalError, setOptionalError] = useState("");
  async function generate(kind: string) {
    setBusy(kind);
    setOptionalError("");
    try {
      await post(`/attempts/${attemptId}/optional-feedback/${kind}`);
      await onUpdate();
    } catch (e) {
      setOptionalError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  function request(kind: string, label: string) {
    return (
      <Button
        variant="outline"
        disabled={!!busy}
        onClick={() => generate(kind)}
      >
        {busy === kind ? (
          <>
            <LoaderCircle className="animate-spin" />
            Đang chuẩn bị…
          </>
        ) : (
          label
        )}
      </Button>
    );
  }
  return (
    <Tabs defaultValue="overview">
      <TabsList>
        {[
          ["overview", "Tổng quan"],
          ["grammar", "Ngữ pháp"],
          ["vocabulary", "Từ vựng"],
          ["coach", "Từ vựng nên học"],
          ["sentences", "Chữa từng câu"],
          ["corrected", "Bài đã sửa"],
          ["improved", "Bài tham khảo B2"],
        ].map(([value, label]) => (
          <TabsTrigger key={value} value={value}>
            {label}
          </TabsTrigger>
        ))}
      </TabsList>
      {optionalError && <ErrorNotice message={optionalError} />}
      <TabsContent value="overview">
        {!ready.includes("detailed") && (
          <div className="mb-5">
            {request("detailed", "Giải thích chi tiết và gợi ý diễn đạt")}
          </div>
        )}
        <div className="grid items-start gap-6 lg:grid-cols-[1.5fr_1fr]">
          <section className="panel p-6 sm:p-7">
            <div className="mb-6 flex items-center gap-3">
              <span className="rounded-lg bg-amber-50 p-2 text-amber-700">
                <Target size={18} />
              </span>
              <h2 className="text-lg font-bold">3 điều cần cải thiện nhất</h2>
            </div>
            <div className="space-y-6">
              {grading.priority_improvements.map((item, index) => (
                <div key={index} className="flex gap-4">
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-teal-50 text-xs font-bold text-teal-800">
                    {index + 1}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold">{item.title_vi}</h3>
                    <p className="mt-2 text-sm leading-7 text-stone-500">
                      {item.explanation_vi}
                    </p>
                    {item.example && (
                      <p
                        lang="en"
                        className="mt-3 border-l-2 border-teal-200 pl-3 text-sm italic leading-6 text-teal-800"
                      >
                        {item.example}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
          <section className="panel p-6 sm:p-7">
            <h2 className="mb-5 flex items-center gap-2 font-bold">
              <CheckCircle2 size={18} className="text-teal-600" />
              Điểm bạn đã làm tốt
            </h2>
            <ul className="space-y-4">
              {grading.strengths.map((s, i) => (
                <li
                  key={i}
                  className="flex gap-3 text-sm leading-7 text-stone-500"
                >
                  <span className="mt-3 size-1.5 shrink-0 rounded-full bg-teal-500" />
                  {s}
                </li>
              ))}
            </ul>
          </section>
        </div>
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <section>
            <h3 className="mb-4 font-bold">Bố cục & phát triển ý</h3>
            <ImprovementList items={grading.structure_feedback} />
          </section>
          <section>
            <h3 className="mb-4 font-bold">Mức độ đáp ứng đề bài</h3>
            <ImprovementList items={grading.task_fulfillment_feedback} />
          </section>
        </div>
        <div className="mt-7">
          <Button variant="outline" onClick={() => setShowAll(!showAll)}>
            {showAll
              ? "Thu gọn lỗi"
              : `Xem tất cả lỗi (${grading.errors.length})`}
          </Button>
          {showAll && (
            <div className="mt-5">
              <ErrorList errors={grading.errors} />
            </div>
          )}
        </div>
      </TabsContent>
      <TabsContent value="grammar">
        <h2 className="mb-5 text-lg font-bold">
          Ngữ pháp, cấu trúc câu & dấu câu
        </h2>
        <ErrorList
          errors={grading.errors.filter((e) =>
            [
              "grammar",
              "sentence_structure",
              "punctuation",
              "spelling",
            ].includes(e.category),
          )}
        />
      </TabsContent>
      <TabsContent value="vocabulary">
        <h2 className="mb-5 text-lg font-bold">
          Diễn đạt tự nhiên hơn ở trình độ B2
        </h2>
        {!grading.vocabulary_suggestions.length &&
          !ready.includes("detailed") && (
            <div className="mb-5">
              {request("detailed", "Tạo gợi ý diễn đạt theo ngữ cảnh")}
            </div>
          )}
        <div className="mb-7 grid gap-4 md:grid-cols-2">
          {grading.vocabulary_suggestions.map((v, i) => (
            <div key={i} className="panel p-5">
              <div
                lang="en"
                className="flex flex-wrap items-center gap-2 text-sm"
              >
                <span className="text-stone-400">{v.original}</span>
                <ArrowRight size={14} />
                <strong className="text-teal-800">{v.suggestion}</strong>
              </div>
              <p className="my-3 text-sm leading-6 text-stone-500">
                {v.reason_vi}
              </p>
              <p
                lang="en"
                className="rounded-lg bg-teal-50 p-3 text-sm italic leading-6 text-teal-900"
              >
                {v.example}
              </p>
            </div>
          ))}
        </div>
        <ErrorList
          errors={grading.errors.filter((e) =>
            ["vocabulary", "word_choice", "collocation", "register"].includes(
              e.category,
            ),
          )}
        />
      </TabsContent>
      <TabsContent value="coach">
        <VocabularyRecommendations
          source={{ source_skill: "WRITING", source_attempt_id: attemptId }}
        />
      </TabsContent>
      <TabsContent value="sentences">
        <h2 className="mb-5 text-lg font-bold">Hiểu từng câu trong bài viết</h2>
        {!grading.sentence_feedback.length &&
          !ready.includes("sentences") &&
          request("sentences", "Chữa từng câu trong bài của tôi")}
        <div className="space-y-5">
          {grading.sentence_feedback.map((s, i) => (
            <article key={i} className="panel p-6">
              <p className="eyebrow mb-4">Câu {i + 1}</p>
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs font-semibold text-stone-400">
                    Câu gốc
                  </p>
                  <p lang="en" className="text-sm leading-7">
                    {s.original}
                  </p>
                </div>
                <div>
                  <p className="mb-2 text-xs font-semibold text-teal-700">
                    Câu đã sửa
                  </p>
                  <p lang="en" className="text-sm leading-7 text-teal-900">
                    {s.corrected}
                  </p>
                </div>
              </div>
              <p className="mt-4 border-t border-stone-100 pt-4 text-sm leading-7 text-stone-500">
                {s.explanation_vi}
              </p>
            </article>
          ))}
        </div>
      </TabsContent>
      <TabsContent value="corrected">
        <p className="mb-4 text-sm text-stone-500">
          Giữ nguyên ý và phần lớn cách diễn đạt của bạn, chỉ sửa các lỗi cần
          thiết.
        </p>
        {!grading.corrected_version && !ready.includes("corrected") ? (
          request("corrected", "Tạo bản đã sửa")
        ) : (
          <article lang="en" className="prose-writing panel p-6 sm:p-9">
            {grading.corrected_version || "Không có nội dung để chỉnh sửa."}
          </article>
        )}
      </TabsContent>
      <TabsContent value="improved">
        <p className="mb-4 text-sm text-stone-500">
          Bài tham khảo phát triển từ ý chính của bạn, hướng đến cách diễn đạt
          B2 / B2+.
        </p>
        {!grading.improved_b2_version && !ready.includes("improved") ? (
          request("improved", "Tạo bài tham khảo B2")
        ) : (
          <article lang="en" className="prose-writing panel p-6 sm:p-9">
            {grading.improved_b2_version ||
              "Bài viết chưa đủ nội dung để phát triển phiên bản tham khảo."}
          </article>
        )}
      </TabsContent>
      <details className="panel mt-7 p-5">
        <summary className="cursor-pointer text-sm font-semibold">
          Xem lại bài viết gốc của bạn
        </summary>
        <p lang="en" className="prose-writing mt-5">
          {answer || "Bạn đã nộp bài trống."}
        </p>
      </details>
    </Tabs>
  );
}

function LocalRecovery({ attempt }: { attempt: AttemptDetail }) {
  const { user } = useAuth();
  const [local] = useState<string>(() => {
    try {
      const draft = JSON.parse(
        localStorage.getItem(draftKey(user!.id, attempt.id)) || "null",
      );
      return typeof draft?.answer === "string" ? draft.answer : "";
    } catch {
      return "";
    }
  });
  if (!local || local === attempt.answer) return null;
  function download() {
    const url = URL.createObjectURL(
      new Blob([local], { type: "text/plain;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `vstep-task-${attempt.task_type}-ban-nhap.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <details className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-5 text-amber-900">
      <summary className="cursor-pointer text-sm font-semibold">
        Có bản nháp trên thiết bị chưa được đưa vào bài nộp
      </summary>
      <p className="my-3 text-xs leading-6">
        Bài chấm sử dụng nội dung máy chủ đã lưu trước hạn. Bạn vẫn có thể đọc
        và tải bản nháp này.
      </p>
      <p lang="en" className="mb-4 whitespace-pre-wrap text-sm leading-7">
        {local}
      </p>
      <Button size="sm" variant="outline" onClick={download}>
        <Download />
        Tải bản nháp
      </Button>
    </details>
  );
}

function Result({ id }: { id: string }) {
  const [data, setData] = useState<AttemptDetail | null>(null);
  const [error, setError] = useState("");
  const [grading, setGrading] = useState(false);
  const [gradingTask, setGradingTask] = useState(1);
  const [stage, setStage] = useState("");
  const [upgrading, setUpgrading] = useState(false);
  const started = useRef(false);
  const load = useCallback(async () => {
    const result = await api<AttemptDetail>(`/attempts/${id}`);
    setData(result);
    return result;
  }, [id]);
  const grade = useCallback(
    async (initial: AttemptDetail, upgrade = false) => {
      setError("");
      setGrading(true);
      setUpgrading(upgrade);
      try {
        for (const attempt of initial.exam.attempts) {
          if (
            (!attempt.grading || (upgrade && attempt.id === initial.id)) &&
            attempt.status !== "DRAFT"
          ) {
            setGradingTask(attempt.task_type);
            setStage("Đang đối chiếu bằng chứng và chấm bốn tiêu chí");
            await post(
              `/attempts/${attempt.id}/${upgrade ? "regrade" : "grade"}`,
            );
            await load();
          }
        }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setGrading(false);
      }
    },
    [load],
  );
  useEffect(() => {
    let active = true;
    api<AttemptDetail>(`/attempts/${id}`)
      .then((result) => {
        if (!active) return;
        setData(result);
        if (!started.current && result.status !== "DRAFT") {
          started.current = true;
          void grade(result);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id, grade]);
  if (!data)
    return error ? (
      <>
        <ErrorNotice message={error} />
        <Button onClick={() => load().catch((e) => setError(e.message))}>
          Thử lại
        </Button>
      </>
    ) : (
      <Loading text="Đang mở kết quả..." />
    );
  if (data.status === "DRAFT")
    return (
      <EmptyState
        title="Bài viết chưa được nộp"
        description="Hoàn thành và nộp bài để nhận phản hồi. Bài viết của bạn đã được lưu."
      >
        <Button asChild>
          <Link href={`/exam?id=${data.exam_session_id}`}>
            Tiếp tục viết
            <ArrowRight />
          </Link>
        </Button>
      </EmptyState>
    );
  const g = data.grading;
  return (
    <div className="space-y-7">
      <div>
        <Link
          href="/history"
          className="mb-5 inline-flex items-center gap-2 text-xs font-medium text-stone-500"
        >
          <ArrowLeft size={14} />
          Lịch sử luyện tập
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="eyebrow">Nhìn lại & tiến bộ</p>
            <h1 className="mb-3 mt-3 text-3xl font-bold">
              Phản hồi bài viết của bạn
            </h1>
            <p className="text-xs text-stone-500">
              Task {data.task_type} · {topics[data.question.topic]} ·{" "}
              {data.word_count} từ ·{" "}
              {formatDate(data.submitted_at || data.created_at)}
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href={`/practice/task-${data.task_type}`}>
              Luyện bài tiếp theo
              <ArrowRight />
            </Link>
          </Button>
        </div>
      </div>
      <LibraryOrigin value={data.question} retry />
      {g && (
        <AttemptLearningSignals
          key={g.id}
          skill="WRITING"
          attemptId={data.id}
        />
      )}
      <LocalRecovery attempt={data} />
      {data.exam.mode === "FULL_TEST" && (
        <div className="panel flex flex-wrap items-center justify-between gap-4 p-5">
          <div>
            <p className="text-xs text-stone-500">
              Điểm Writing AI ước tính · (Task 1 + Task 2 × 2) / 3
            </p>
            <p className="mt-2 text-2xl font-bold text-teal-800">
              {data.exam.overall_score == null
                ? "Đang chờ đủ hai Task"
                : `${score(data.exam.overall_score)} / 10`}
            </p>
          </div>
          {data.exam.writing_reference_level && (
            <p className="max-w-sm text-xs leading-6 text-stone-500">
              Năng lực Writing tham khảo:{" "}
              <strong>{data.exam.writing_reference_level}</strong>. Điểm AI ước
              tính, không phải chứng nhận VSTEP.
            </p>
          )}
          <div className="flex gap-3">
            {data.exam.attempts.map((a) => (
              <Button
                key={a.id}
                asChild
                size="sm"
                variant={a.id === id ? "secondary" : "outline"}
              >
                <Link href={`/result?id=${a.id}`}>
                  Task {a.task_type} · {score(a.grading?.scores.overall)}
                </Link>
              </Button>
            ))}
          </div>
        </div>
      )}
      {grading && (
        <div
          role="status"
          className="flex items-center gap-4 rounded-xl border border-teal-100 bg-teal-50 p-5 text-teal-900"
        >
          <LoaderCircle className="size-6 shrink-0 animate-spin" />
          <div>
            <p className="font-semibold">
              Task {gradingTask} · {stage}...
            </p>
            <p className="mt-1 text-xs leading-6 text-teal-700">
              Quá trình có thể mất vài phút. Bài đã được lưu; bạn có thể quay
              lại kết quả từ lịch sử.
            </p>
          </div>
        </div>
      )}
      {error && (
        <div>
          <ErrorNotice message={error} />
          <Button
            variant="outline"
            onClick={() => grade(data, upgrading)}
            disabled={grading}
          >
            <Sparkles />
            Thử chấm lại
          </Button>
        </div>
      )}
      {g ? (
        <>
          <section className="grid gap-6 lg:grid-cols-[280px_1fr]">
            <div className="rounded-2xl bg-teal-800 p-7 text-white">
              <p className="text-sm text-teal-100">
                Điểm AI ước tính · Task {data.task_type}
              </p>
              <p className="my-5 text-6xl font-bold tracking-tight">
                {score(g.scores.overall)}
                <span className="ml-2 text-lg font-normal text-teal-200">
                  / 10
                </span>
              </p>
              <p className="mt-4 text-xs leading-6 text-teal-100">
                Đây là điểm luyện tập cho nhiệm vụ này, không phải kết quả xác
                định bậc VSTEP.
              </p>
            </div>
            <div className="panel p-6 sm:p-7">
              <h2 className="mb-5 font-bold">Bốn tiêu chí chấm bài</h2>
              <div className="grid gap-x-7 gap-y-5 sm:grid-cols-2">
                {Object.entries(criteria).map(([key, label]) => {
                  const value = g.scores[key as keyof typeof g.scores];
                  return (
                    <div key={key}>
                      <div className="mb-2 flex justify-between text-sm">
                        <span className="text-stone-500">{label}</span>
                        <strong>
                          {score(value)}
                          <span className="font-normal text-stone-300">
                            {" "}
                            / 10
                          </span>
                        </strong>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-stone-100">
                        <div
                          className="h-full rounded-full bg-teal-600"
                          style={{ width: `${value * 10}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="mt-6 border-t border-stone-100 pt-5 text-sm leading-7 text-stone-600">
                {g.summary_vi}
              </p>
            </div>
          </section>
          <div className="panel flex flex-wrap items-center justify-between gap-4 p-5">
            <div>
              <p className="text-sm font-semibold">
                Bộ chấm {g.grader_version || "1.0.0"}
              </p>
              <p className="mt-1 text-xs text-stone-500">
                {g.ai_model} · Phân tích {g.analysis_prompt_version || "—"} ·
                Hiệu chỉnh {g.calibration_prompt_version || "—"}
              </p>
            </div>
            {g.grader_version !== g.current_grader_version && (
              <Button
                variant="outline"
                disabled={grading}
                onClick={() => grade(data, true)}
              >
                Chấm lại với bộ chấm mới
              </Button>
            )}
          </div>
          <WritingEvidencePanel grading={g} />
          <WritingGradingHistory
            key={`${data.id}:${g.grader_version}`}
            attemptId={data.id}
          />
          <Feedback
            key={data.id}
            grading={g}
            answer={data.answer}
            attemptId={data.id}
            ready={data.optional_feedback_ready || []}
            onUpdate={load}
          />
        </>
      ) : !grading && !error ? (
        <Button onClick={() => grade(data)}>
          <Sparkles />
          Chấm bài viết
        </Button>
      ) : null}
      {!g && (
        <details className="panel p-5" open>
          <summary className="cursor-pointer text-sm font-semibold">
            Bài viết đã nộp của bạn
          </summary>
          <p lang="en" className="prose-writing mt-5">
            {data.answer || "Bạn đã nộp bài trống."}
          </p>
        </details>
      )}
      <details className="panel p-5">
        <summary className="cursor-pointer text-sm font-semibold">
          Xem lại đề bài
        </summary>
        <div className="mt-6">
          <QuestionCard question={data.question} />
        </div>
      </details>
      <p className="rounded-xl bg-stone-100 p-4 text-xs leading-6 text-stone-500">
        {DISCLAIMER}
      </p>
      {g && <Paywall title="Tiếp tục với Writing Task 2 và thi thử đầy đủ" compact />}
    </div>
  );
}
export function ResultView({ id }: { id: string }) {
  return (
    <RequireAuth>
      <Result key={id} id={id} />
    </RequireAuth>
  );
}
