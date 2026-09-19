"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  BookOpen,
  LoaderCircle,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { post } from "@/services/api";
import { LearningHeader, LoadError, useLearning } from "./shared";
import {
  allowedKinds,
  kinds,
  statusLabels,
  trends,
  type Detail,
  type Exercise,
  type Lesson,
  type Skill,
} from "./types";
export function WeaknessDetail({ id }: { id: string }) {
  return (
    <RequireAuth>
      <DetailView id={id} />
    </RequireAuth>
  );
}
function DetailView({ id }: { id: string }) {
  const { data, error, reload, setData } = useLearning<Detail>(
    `/weaknesses/${id}`,
  );
  const [busy, setBusy] = useState("");
  const [actionError, setActionError] = useState("");
  const [kind, setKind] = useState("");
  const [count, setCount] = useState(8);
  const requestId = useRef<string | null>(null);
  const targetRequests = useRef<Record<string, string>>({});
  const router = useRouter();
  async function lesson() {
    setBusy("lesson");
    setActionError("");
    try {
      const result = await post<Lesson>(`/learning/weaknesses/${id}/lesson`);
      setData((d) => (d ? { ...d, lesson: result } : d));
      reload();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function practice(secondChance = false) {
    setBusy("practice");
    setActionError("");
    requestId.current ??= crypto.randomUUID();
    try {
      const exercise = await post<Exercise>(
        `/learning/weaknesses/${id}/practice`,
        {
          client_request_id: requestId.current,
          kind: kind || null,
          count,
          second_chance: secondChance,
        },
      );
      requestId.current = null;
      router.push(`/learning/practice/${exercise.id}`);
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function targeted(
    skill: Skill,
    part?: number,
    source: "BANK" | "AI" = skill === "READING" ? "BANK" : "AI",
  ) {
    setBusy(`target-${skill}`);
    setActionError("");
    try {
      const key = `${skill}:${part}:${source}`;
      targetRequests.current[key] ??= crypto.randomUUID();
      const result = await post<{ url: string }>(
        `/learning/weaknesses/${id}/targeted-practice`,
        {
          client_request_id: targetRequests.current[key],
          skill,
          part: part ?? null,
          source,
        },
      );
      router.push(result.url);
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  if (error) return <LoadError message={error} retry={reload} />;
  if (!data) return <Loading />;
  const choices =
    allowedKinds[data.category] ||
    allowedKinds[data.skill] ||
    allowedKinds.GRAMMAR;
  return (
    <div className="space-y-7">
      <Link
        href="/learning"
        className="inline-flex items-center gap-2 text-sm text-stone-500"
      >
        <ArrowLeft size={15} />
        Phân tích học tập
      </Link>
      <LearningHeader
        title={data.display_name_vi}
        description={`${data.occurrence_count} lần ghi nhận trong ${data.affected_attempt_count} bài · ${data.stats.skills.join(" + ")}`}
      />
      {actionError && <ErrorNotice message={actionError} />}
      <section className="grid gap-3 sm:grid-cols-3">
        {[
          ["Mức độ", statusLabels[data.status]],
          ["Xu hướng", trends[data.trend]],
          ["Bằng chứng", data.stats.confidence_label],
        ].map(([a, b]) => (
          <div key={a} className="panel p-5">
            <p className="text-xs text-stone-500">{a}</p>
            <p className="mt-2 font-semibold">{b}</p>
          </div>
        ))}
      </section>
      {data.stats.skills.length > 1 && (
        <p className="rounded-xl bg-teal-50 p-4 text-sm leading-7 text-teal-900">
          Cùng một cách dùng xuất hiện ở cả Writing và Speaking. Bài luyện dưới
          đây giúp bạn nhận diện, viết và nói trong ngữ cảnh mới.
        </p>
      )}
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <section className="panel p-6">
          <h2 className="text-lg font-semibold">Bằng chứng từ bài của bạn</h2>
          <p className="mt-2 text-xs text-stone-500">
            Tối đa 30 ví dụ gần nhất · bấm bài gốc để xem đầy đủ ngữ cảnh.
          </p>
          <div className="mt-5 max-h-[560px] space-y-5 overflow-y-auto">
            {data.evidence.map((e) => (
              <article
                key={e.id}
                className="rounded-xl border border-stone-200 p-4"
              >
                <div className="flex flex-wrap justify-between gap-2 text-xs text-stone-500">
                  <span>
                    {e.skill}
                    {e.details.part ? ` · Part ${e.details.part}` : ""} ·{" "}
                    {new Date(e.created_at).toLocaleDateString("vi-VN")}
                  </span>
                  <Link
                    href={e.details.source_url}
                    className="text-teal-800 underline"
                  >
                    Bài gốc ↗
                  </Link>
                </div>
                {e.original_text && (
                  <p
                    lang="en"
                    className="mt-3 whitespace-pre-wrap rounded-lg bg-stone-50 p-3 text-sm leading-7"
                  >
                    {e.original_text}
                  </p>
                )}
                {e.corrected_text && (
                  <p lang="en" className="mt-2 text-sm leading-7 text-teal-800">
                    → {e.corrected_text}
                  </p>
                )}
                {e.details.correct_answer && (
                  <p className="mt-2 text-xs text-stone-500">
                    Đã chọn: {e.details.selected_answer || "bỏ trống"} · Đáp án:{" "}
                    {e.details.correct_answer}
                  </p>
                )}
                {e.details.explanation_vi && (
                  <p className="mt-3 text-sm leading-7 text-stone-600">
                    {e.details.explanation_vi}
                  </p>
                )}
                {e.details.audible_evidence_vi && (
                  <p className="mt-2 text-xs leading-6 text-stone-500">
                    Bằng chứng audio: {e.details.audible_evidence_vi}
                  </p>
                )}
                {e.outcome === "SUCCESS" && (
                  <p className="mt-2 text-xs font-semibold text-teal-700">
                    Có bằng chứng dùng đúng
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
        <aside className="space-y-5">
          <section className="panel p-5">
            <h2 className="font-semibold">Theo dõi tiến bộ</h2>
            {data.stats.older_rate !== null ? (
              <div className="mt-4">
                <p className="text-2xl font-semibold">
                  {data.stats.older_rate} → {data.stats.recent_rate}
                </p>
                <p className="mt-2 text-xs text-stone-500">
                  {data.stats.unit} · hai nhóm {data.stats.window_attempts} bài
                  liên tiếp
                </p>
              </div>
            ) : (
              <p className="mt-3 text-sm leading-7 text-stone-500">
                Cần hai nhóm {data.stats.window_attempts} bài để so sánh có cùng
                cách tính.
              </p>
            )}
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <dt>Câu đã luyện</dt>
                <dd>{data.stats.exercise_count}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt>Đúng trong lượt gần đây</dt>
                <dd>
                  {data.stats.exercise_accuracy === null
                    ? "—"
                    : `${data.stats.exercise_accuracy}%`}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt>Bài mới dùng đúng sau lỗi gần nhất</dt>
                <dd>{data.stats.reuse_attempts}</dd>
              </div>
            </dl>
            <p className="mt-4 text-xs leading-6 text-stone-500">
              {data.mastery_requirements_vi}
            </p>
          </section>
          <section className="rounded-2xl bg-teal-950 p-5 text-white">
            <h2 className="font-semibold">Áp dụng vào bài mới</h2>
            <p className="mt-2 text-sm leading-7 text-teal-100/80">
              {data.skill === "READING"
                ? "Chọn câu đã kiểm duyệt trong ngân hàng hoặc tạo bộ AI mới, tập trung đúng loại câu cần luyện."
                : "Đề AI tạo cơ hội luyện nội dung này. Bài làm vẫn được chấm theo quy trình của kỹ năng."}
            </p>
            <div className="mt-4 space-y-2">
              {(data.skill === "CROSS"
                ? ["WRITING", "SPEAKING"]
                : [data.skill]
              ).map((s) => (
                <Button
                  className="w-full"
                  variant="secondary"
                  disabled={!!busy}
                  key={s}
                  onClick={() => targeted(s as Skill)}
                >
                  {busy === `target-${s}` ? (
                    <LoaderCircle className="animate-spin" />
                  ) : (
                    <Sparkles size={15} />
                  )}
                  {s === "READING"
                    ? "Luyện 10 câu Reading"
                    : s === "SPEAKING"
                      ? data.category === "PRONUNCIATION"
                        ? "Ghi âm luyện phát âm"
                        : "Luyện Speaking có ghi âm"
                      : "Luyện Writing Task 2"}
                </Button>
              ))}
              {data.skill === "READING" && (
                <Button
                  className="w-full"
                  variant="secondary"
                  disabled={!!busy}
                  onClick={() => targeted("READING", undefined, "AI")}
                >
                  <Sparkles size={15} />
                  Tạo 10 câu mới bằng AI
                </Button>
              )}
            </div>
            <p className="mt-4 text-xs leading-6 text-teal-100/70">
              Chỉ áp dụng trong chế độ học. Đề thi đầy đủ giữ cấu trúc VSTEP
              bình thường.
            </p>
          </section>
        </aside>
      </div>
      <section className="panel p-6 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Bài học dành cho bạn</h2>
            <p className="mt-2 text-sm text-stone-500">
              Quy tắc ngắn, ví dụ tự nhiên và lỗi từ bài thật của bạn.
            </p>
          </div>
          <Button disabled={!!busy} onClick={lesson}>
            {busy === "lesson" ? (
              <LoaderCircle className="animate-spin" />
            ) : (
              <BookOpen size={16} />
            )}
            {data.lesson ? "Ôn bài học" : "Tạo bài học"}
          </Button>
        </div>
        {data.lesson && <LessonContent lesson={data.lesson} />}
      </section>
      <section className="panel p-6">
        <h2 className="text-xl font-semibold">Luyện điểm yếu này</h2>
        <p className="mt-2 text-sm leading-7 text-stone-500">
          Bài luyện ngắn có phản hồi từng câu. Lượt thứ hai dùng ngữ cảnh mới để
          kiểm tra bạn đã hiểu quy tắc.
        </p>
        <div className="mt-5 flex flex-wrap items-end gap-4">
          <label className="grid gap-2 text-sm">
            Dạng bài
            <select
              className="field min-w-52"
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                requestId.current = null;
              }}
            >
              <option value="">Kết hợp các dạng</option>
              {choices.map((k) => (
                <option key={k} value={k}>
                  {kinds[k]}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm">
            Số câu
            <select
              className="field"
              value={count}
              onChange={(e) => {
                setCount(Number(e.target.value));
                requestId.current = null;
              }}
            >
              {[5, 8, 10].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
          <Button disabled={!!busy} onClick={() => practice()}>
            {busy === "practice" ? (
              <LoaderCircle className="animate-spin" />
            ) : (
              <Sparkles size={16} />
            )}
            Tạo bài luyện
          </Button>
          <Button
            variant="outline"
            disabled={!!busy}
            onClick={() => practice(true)}
          >
            <RotateCcw size={16} />
            Thử lại trong ngữ cảnh mới
          </Button>
        </div>
      </section>
    </div>
  );
}
function LessonContent({ lesson }: { lesson: Lesson }) {
  const c = lesson.content;
  return (
    <div className="mt-7 space-y-6">
      <div>
        <h3 className="text-lg font-semibold">{c.title}</h3>
        <p className="mt-3 text-sm leading-8 text-stone-600">
          {c.why_this_matters_vi}
        </p>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-8">
          {c.simple_explanation_vi}
        </p>
      </div>
      <ol className="list-decimal space-y-3 pl-5 text-sm leading-7">
        {c.rules.map((r, i) => (
          <li key={i}>{r}</li>
        ))}
      </ol>
      <div className="grid gap-4 sm:grid-cols-2">
        {c.examples.map((e, i) => (
          <div key={i} className="rounded-xl bg-teal-50 p-4">
            <p
              lang="en"
              className="text-sm font-medium leading-7 text-teal-950"
            >
              {e.english}
            </p>
            <p className="mt-2 text-sm leading-7 text-teal-800">
              {e.explanation_vi}
            </p>
          </div>
        ))}
      </div>
      {c.examples_from_user_errors.length > 0 && (
        <div>
          <h4 className="mb-3 font-semibold">Áp dụng vào lỗi bạn đã gặp</h4>
          <div className="space-y-3">
            {c.examples_from_user_errors.map((e) => (
              <div
                key={e.signal_id}
                className="rounded-xl border border-stone-200 p-4"
              >
                <p lang="en" className="text-sm">
                  {e.original}
                </p>
                {e.corrected && (
                  <p lang="en" className="mt-2 text-sm text-teal-800">
                    → {e.corrected}
                  </p>
                )}
                <p className="mt-3 text-sm leading-7 text-stone-600">
                  {e.explanation_vi}
                </p>
                {c.sources.find((s) => s.signal_id === e.signal_id)
                  ?.source_url && (
                  <Link
                    href={
                      c.sources.find((s) => s.signal_id === e.signal_id)!
                        .source_url
                    }
                    className="mt-2 inline-block text-xs text-teal-800 underline"
                  >
                    Xem bài gốc
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="grid gap-5 md:grid-cols-2">
        <div>
          <h4 className="mb-3 font-semibold">Dễ nhầm ở đâu?</h4>
          <ul className="list-disc space-y-2 pl-5 text-sm leading-7 text-stone-600">
            {c.common_traps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-3 font-semibold">Tự kiểm tra nhanh</h4>
          <ul className="list-disc space-y-2 pl-5 text-sm leading-7 text-stone-600">
            {c.quick_check.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      </div>
      <p className="rounded-xl bg-stone-50 p-4 text-sm leading-7">
        {c.practice_recommendation}
      </p>
    </div>
  );
}
