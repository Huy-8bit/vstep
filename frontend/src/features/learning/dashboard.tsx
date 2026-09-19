"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Clock3, RefreshCw } from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Loading, ErrorNotice } from "@/components/feedback";
import { post } from "@/services/api";
import { LearningHeader, LoadError, useLearning, WeaknessGrid } from "./shared";
import {
  criteria,
  trends,
  type Overview,
  type Today,
  type SkillAnalysis,
  type VocabularyAnalysis,
  type Weakness,
  type WeeklySummary,
} from "./types";

export function LearningDashboard() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}
function Dashboard() {
  const { data, error, reload } = useLearning<Overview>("/overview");
  const today = useLearning<Today>("/today");
  const reloadToday = today.reload;
  const [tab, setTab] = useState("writing");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  useEffect(() => {
    if (data?.backfill_status !== "RUNNING") return;
    const timer = setTimeout(() => {
      reload();
      reloadToday();
    }, 2500);
    return () => clearTimeout(timer);
  }, [data, reload, reloadToday]);
  async function recalculate() {
    setBusy(true);
    setActionError("");
    try {
      await post("/learning/recalculate");
      reload();
      today.reload();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <LoadError message={error} retry={reload} />;
  if (!data) return <Loading />;
  const weekly = data.weekly;
  return (
    <div className="space-y-9">
      <LearningHeader />
      {actionError && <ErrorNotice message={actionError} />}
      {data.backfill_status === "RUNNING" && (
        <p
          role="status"
          className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900"
        >
          Đang tổng hợp lịch sử đã chấm · đã xem {data.backfill_processed} bài.
          Bạn vẫn có thể tiếp tục luyện tập.
        </p>
      )}
      {data.backfill_status === "FAILED" && (
        <div className="panel p-4 text-sm">
          Chưa tổng hợp xong lịch sử.{" "}
          <button
            onClick={recalculate}
            disabled={busy}
            className="font-semibold text-teal-800 underline"
          >
            Thử lại
          </button>
        </div>
      )}
      <section className="rounded-2xl bg-teal-950 p-6 text-white sm:p-8">
        <p className="text-xs tracking-widest text-teal-200">30 NGÀY GẦN ĐÂY</p>
        <div className="mt-5 grid grid-cols-2 gap-6 md:grid-cols-5">
          {[
            [data.recent.writing_attempts, "bài Writing"],
            [data.recent.speaking_attempts, "bài Speaking"],
            [data.recent.reading_questions, "câu Reading có đáp án"],
            [data.improving_skills, "kỹ năng cải thiện"],
            [data.mastered_count, "nội dung thành thạo"],
          ].map(([n, label]) => (
            <div key={label}>
              <p className="text-3xl font-semibold">{n}</p>
              <p className="mt-2 text-xs text-teal-100/80">{label}</p>
            </div>
          ))}
        </div>
      </section>
      <section>
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Ưu tiên học tuần này</h2>
            <p className="mt-2 text-sm text-stone-500">
              Bắt đầu với tối đa ba nội dung có ích nhất.
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={recalculate}
            disabled={busy || data.backfill_status === "RUNNING"}
          >
            <RefreshCw className={busy ? "animate-spin" : ""} size={14} />
            Cập nhật lịch sử
          </Button>
        </div>
        <WeaknessGrid items={data.top_priorities} />
        <p className="mt-3 text-xs leading-6 text-stone-400">
          {data.priority_note_vi}
        </p>
      </section>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="panel p-6">
          <div className="flex items-center gap-2">
            <Clock3 size={18} className="text-teal-700" />
            <h2 className="text-lg font-semibold">Học hôm nay</h2>
          </div>
          {today.error ? (
            <LoadError message={today.error} retry={today.reload} />
          ) : today.data ? (
            <>
              <p className="mt-2 text-sm text-stone-500">
                Khoảng {today.data.estimated_minutes} phút · từng bước nhỏ, có
                mục tiêu.
              </p>
              <div className="mt-5 space-y-3">
                {(today.data.items.length
                  ? today.data.items
                  : today.data.recommendations
                ).map((item, i) => (
                  <Link
                    key={i}
                    href={item.url}
                    className="flex items-center justify-between gap-3 rounded-xl border border-stone-200 p-4 hover:border-teal-600"
                  >
                    <div>
                      <p className="font-medium">{item.title}</p>
                      <p className="mt-1 text-xs text-stone-500">
                        {item.estimated_minutes} phút
                      </p>
                    </div>
                    <ArrowRight size={16} />
                  </Link>
                ))}
              </div>
              {!today.data.recommendations.length && (
                <p className="mt-4 text-sm text-stone-500">
                  Hãy bắt đầu bằng một bài Writing, Speaking hoặc Reading.
                </p>
              )}
            </>
          ) : (
            <Loading />
          )}
          <Link
            href="/learning/plan"
            className="mt-5 inline-block text-sm font-semibold text-teal-800"
          >
            Xem kế hoạch học →
          </Link>
        </section>
        <section className="panel p-6">
          <h2 className="text-lg font-semibold">Điểm mạnh của bạn</h2>
          <p className="mt-2 text-sm leading-6 text-stone-500">
            Duy trì những gì đã làm tốt để dành thời gian cho phần cần luyện.
          </p>
          <div className="mt-5 space-y-4">
            {data.strengths.length ? (
              data.strengths.map((s) => (
                <div key={s.skill + s.label} className="flex gap-3">
                  <CheckCircle2
                    size={18}
                    className="mt-1 shrink-0 text-teal-700"
                  />
                  <div>
                    <p className="text-sm font-medium">
                      {s.skill} · {criteria[s.label] || s.label}
                    </p>
                    <p className="mt-1 text-xs text-stone-500">
                      {s.value}
                      {s.unit} · {s.evidence_count} mẫu gần đây
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-stone-500">
                Cần thêm các bài đã chấm để xác định điểm mạnh ổn định.
              </p>
            )}
          </div>
        </section>
      </div>
      <section>
        <div
          className="mb-5 flex gap-2 overflow-x-auto border-b border-stone-200 pb-3"
          aria-label="Nhóm phân tích"
        >
          {[
            ["writing", "Writing"],
            ["speaking", "Speaking"],
            ["reading", "Reading"],
            ["grammar", "Ngữ pháp chung"],
            ["vocabulary", "Từ vựng"],
            ["mastered", "Đã thành thạo"],
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              aria-pressed={tab === key}
              className={`whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium ${tab === key ? "bg-teal-800 text-white" : "bg-stone-100 text-stone-600"}`}
            >
              {label}
            </button>
          ))}
        </div>
        <AnalysisSection key={tab + data.revision} section={tab} />
      </section>
      <section className="panel p-6">
        <h2 className="text-xl font-semibold">Tổng kết 7 ngày gần đây</h2>
        <div className="mt-5 grid grid-cols-2 gap-5 md:grid-cols-5">
          {[
            [weekly.attempts_completed, "bài đã hoàn thành"],
            [weekly.recorded_practice_minutes, "phút luyện được ghi nhận"],
            [weekly.new_weaknesses, "nội dung mới ghi nhận"],
            [weekly.improving, "nội dung đang cải thiện"],
            [weekly.mastered, "nội dung thành thạo"],
          ].map(([n, l]) => (
            <div key={l}>
              <p className="text-2xl font-semibold">{n}</p>
              <p className="mt-1 text-xs text-stone-500">{l}</p>
            </div>
          ))}
        </div>
        {weekly.highest_improvement && (
          <p className="mt-5 text-sm">
            Cải thiện rõ nhất: <strong>{weekly.highest_improvement}</strong>.
          </p>
        )}
        {weekly.next_priority && (
          <p className="mt-3 text-sm text-stone-600">
            Ưu tiên tiếp theo: {weekly.next_priority}.
          </p>
        )}
        <p className="mt-4 text-xs text-stone-400">
          Thời gian tính từ các câu luyện đã gửi, không tính thời gian mở trang.
        </p>
        <WeeklyCoach
          key={data.revision}
          summary={weekly.ai_summary}
          disabled={data.backfill_status !== "COMPLETE"}
        />
      </section>
      <RecentExercises />
    </div>
  );
}
function WeeklyCoach({
  summary,
  disabled,
}: {
  summary: WeeklySummary | null;
  disabled: boolean;
}) {
  const [result, setResult] = useState(summary);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function generate() {
    setBusy(true);
    setError("");
    try {
      setResult(await post<WeeklySummary>("/learning/weekly/summary"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="mt-5 border-t border-stone-200 pt-5">
      {error && <ErrorNotice message={error} />}
      {result ? (
        <div className="space-y-4">
          <h3 className="font-semibold">Gợi ý từ gia sư AI</h3>
          <p className="whitespace-pre-line text-sm leading-7 text-stone-700">
            {result.summary_vi}
          </p>
          {result.recommendations.map((r) => (
            <div
              key={r.weakness_id}
              className="rounded-xl bg-teal-50 p-4 text-sm"
            >
              <Link
                href={r.url}
                className="font-semibold text-teal-900 underline"
              >
                {r.label_vi}
              </Link>
              <p className="mt-2 leading-6 text-stone-600">{r.reason_vi}</p>
              <p className="mt-2 leading-6">{r.activity_vi}</p>
            </div>
          ))}
        </div>
      ) : (
        <Button
          size="sm"
          variant="outline"
          onClick={generate}
          disabled={busy || disabled}
        >
          {busy ? "Đang viết tổng kết…" : "Nhận tổng kết và gợi ý từ AI"}
        </Button>
      )}
    </div>
  );
}
function RecentExercises() {
  const { data, error, reload } = useLearning<{
    items: {
      id: string;
      title: string;
      url: string;
      completed_at: string | null;
    }[];
  }>("/exercises");
  if (error) return <LoadError message={error} retry={reload} />;
  if (!data?.items.length) return null;
  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold">Tiếp tục bài luyện</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {data.items.slice(0, 6).map((i) => (
          <Link
            className="panel flex items-center justify-between gap-4 p-4 text-sm hover:border-teal-600"
            href={i.url}
            key={i.id}
          >
            {i.title}
            <span className="text-xs text-stone-500">
              {i.completed_at ? "Đã hoàn thành" : "Mở bài →"}
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
function AnalysisSection({ section }: { section: string }) {
  const path =
    section === "mastered" ? "/weaknesses?status=MASTERED" : `/${section}`;
  const { data, error, reload } = useLearning<
    SkillAnalysis | VocabularyAnalysis | { items: Weakness[] }
  >(path);
  if (error) return <LoadError message={error} retry={reload} />;
  if (!data) return <Loading />;
  if ("items" in data) return <WeaknessGrid items={data.items} />;
  if ("frequent_expressions" in data)
    return (
      <div className="space-y-6">
        <WeaknessGrid items={data.weaknesses} />
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="panel p-5">
            <h3 className="font-semibold">Cách diễn đạt thường dùng</h3>
            <p className="mt-2 text-xs leading-6 text-stone-500">
              {data.frequency_note_vi}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {data.frequent_expressions.length ? (
                data.frequent_expressions.map((i) => (
                  <span
                    className="rounded-lg bg-stone-100 px-3 py-2 text-sm"
                    key={i.phrase}
                  >
                    {i.phrase} · {i.count} lần / {i.attempts} bài
                  </span>
                ))
              ) : (
                <p className="text-sm text-stone-500">
                  Chưa có cụm từ lặp lại qua nhiều bài.
                </p>
              )}
            </div>
          </section>
          <section className="panel p-5">
            <h3 className="font-semibold">Từ đã học và khả năng dùng lại</h3>
            <p className="mt-2 text-xs leading-6 text-stone-500">
              Chỉ có mặt trong bài chưa chứng minh dùng tự nhiên. Lượt dùng có
              bằng chứng tích cực được hiển thị riêng.
            </p>
            <div className="mt-3 max-h-72 space-y-3 overflow-y-auto">
              {data.notebook.slice(0, 20).map((i) => (
                <div key={i.id} className="border-b border-stone-100 py-2">
                  <p className="text-sm font-medium">{i.phrase}</p>
                  <p className="mt-1 text-xs text-stone-500">
                    {i.learned_not_reused
                      ? "Đã ôn, chưa ghi nhận dùng lại"
                      : `${i.observed_reuses} lần xuất hiện · ${i.verified_reuses} lần có bằng chứng dùng đúng`}{" "}
                    · {i.skills.join(" + ")}
                  </p>
                  {!!i.pending_verifications?.length && (
                    <VerifyReuse
                      eventId={i.pending_verifications[0]}
                      onDone={reload}
                    />
                  )}
                </div>
              ))}
            </div>
            <Button asChild variant="outline" className="mt-4">
              <Link href="/vocabulary">Mở sổ từ và ôn tập</Link>
            </Button>
          </section>
        </div>
      </div>
    );
  return (
    <div className="space-y-5">
      {data.audio_note_vi && (
        <p className="rounded-xl bg-stone-100 p-4 text-sm text-stone-600">
          {data.audio_note_vi}
        </p>
      )}
      {!!data.criteria.length && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {data.criteria.map((c) => (
            <div className="panel p-4" key={c.criterion}>
              <p className="text-sm text-stone-500">
                {criteria[c.criterion] || c.criterion}
              </p>
              <p className="mt-3 text-2xl font-semibold">
                {c.older_average !== null && (
                  <span className="text-base font-normal text-stone-400">
                    {c.older_average} →{" "}
                  </span>
                )}
                {c.recent_average ?? "—"}
              </p>
              <p className="mt-2 text-xs text-stone-500">
                {trends[c.trend]} · {c.samples} bài
              </p>
            </div>
          ))}
        </div>
      )}
      {data.question_types && (
        <div className="panel overflow-x-auto p-5">
          <table className="w-full min-w-96 text-left text-sm">
            <caption className="mb-4 text-left font-semibold">
              Theo loại câu Reading · chỉ câu có đáp án chuẩn
            </caption>
            <thead>
              <tr className="border-b border-stone-200 text-stone-500">
                <th className="pb-3">Loại câu</th>
                <th>Đúng / đã làm</th>
                <th>Độ chính xác</th>
              </tr>
            </thead>
            <tbody>
              {data.question_types.map((q) => (
                <tr className="border-b border-stone-100" key={q.concept_key}>
                  <td className="py-3">{q.label}</td>
                  <td>
                    {q.correct}/{q.total}
                  </td>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="hidden h-2 w-24 rounded bg-stone-100 sm:block">
                        <div
                          className="h-2 rounded bg-teal-600"
                          style={{ width: `${q.accuracy}%` }}
                        />
                      </div>
                      {q.accuracy}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <WeaknessGrid items={data.weaknesses} />
    </div>
  );
}
function VerifyReuse({
  eventId,
  onDone,
}: {
  eventId: string;
  onDone: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function check() {
    setBusy(true);
    setError("");
    try {
      await post(`/learning/vocabulary/reuses/${eventId}/answer`);
      onDone();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="mt-2">
      <Button size="sm" variant="outline" onClick={check} disabled={busy}>
        {busy ? "Đang kiểm tra…" : "Kiểm tra cách dùng lại"}
      </Button>
      {error && (
        <p className="mt-2 text-xs text-red-700" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
