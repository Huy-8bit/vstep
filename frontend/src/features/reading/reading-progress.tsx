"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { RequireAuth } from "@/features/auth/auth-provider";
import { SkillSwitch } from "@/features/speaking/skill-switch";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { api } from "@/services/api";
import {
  disclaimer,
  modes,
  questionTypes,
  topics,
  type Breakdown,
  type ReadingProgress as Progress,
} from "./types";
export function ReadingProgress() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}
function Dashboard() {
  const [data, setData] = useState<Progress | null>(null);
  const [mode, setMode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      setData(await api(`/reading/progress${mode ? `?mode=${mode}` : ""}`));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [mode]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <>
      <SkillSwitch section="progress" active="reading" />
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Đọc lại tiến bộ của chính mình</p>
          <h1 className="mt-2 text-3xl font-bold">Tiến độ Reading</h1>
        </div>
        <label className="text-xs font-semibold">
          Phạm vi thống kê
          <select
            className="field mt-2"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            <option value="">Tất cả lượt luyện</option>
            {Object.entries(modes).map(([value, m]) => (
              <option key={value} value={value}>
                {m.title}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <>
          <ErrorNotice message={error} />
          <Button onClick={load}>Thử lại</Button>
        </>
      )}
      {loading ? (
        <Loading />
      ) : data?.completed_sessions ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat
              label="Điểm Reading trung bình"
              value={data.average_score?.toFixed(2) || "—"}
              note={`${data.completed_sessions} phiên đã nộp · Thang 10`}
            />
            <Stat
              label="Câu đã trả lời"
              value={String(data.questions_answered)}
              note={`${data.questions_total} câu trong các phiên đã nộp`}
            />
            <Stat
              label="Tỷ lệ đúng"
              value={`${data.accuracy}%`}
              note={`${data.correct_count} / ${data.questions_total} câu; gồm cả câu bỏ trống`}
            />
            <Stat
              label="Thời gian trung bình / câu"
              value={`${data.average_time_per_question}s`}
              note="Tổng thời gian phiên / tổng số câu"
            />
          </div>
          {data.weaknesses.length > 0 && (
            <section className="panel p-6">
              <h2 className="mb-5 text-lg font-bold">
                Dạng câu hỏi cần cải thiện
              </h2>
              <div className="grid gap-4 md:grid-cols-3">
                {data.weaknesses.map((row) => (
                  <article key={row.key} className="rounded-xl bg-amber-50 p-5">
                    <p className="text-sm font-semibold">
                      {questionTypes[row.key]}
                    </p>
                    <p className="mt-3 text-2xl font-bold text-teal-800">
                      {row.accuracy}%
                    </p>
                    <p className="mt-2 text-xs text-stone-500">
                      Đúng {row.correct}/{row.total} câu
                    </p>
                    <Button
                      className="mt-4"
                      asChild
                      size="sm"
                      variant="outline"
                    >
                      <Link
                        href={`/reading?mode=QUESTION_TYPE_PRACTICE&type=${row.key}`}
                      >
                        Luyện dạng này →
                      </Link>
                    </Button>
                  </article>
                ))}
              </div>
            </section>
          )}
          <section className="panel p-6">
            <h2 className="text-lg font-bold">Điểm qua các lần luyện</h2>
            <p className="mb-6 mt-2 text-xs text-stone-500">
              Chọn một chế độ để so sánh các lượt luyện tương đồng.
            </p>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={data.timeline.map((p) => ({
                    ...p,
                    label: new Date(p.date).toLocaleDateString("vi-VN"),
                  }))}
                  margin={{ left: -20, right: 15 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line
                    dataKey="score"
                    name="Điểm luyện tập"
                    stroke="#115e59"
                    strokeWidth={3}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="panel p-6">
              <h2 className="mb-5 text-lg font-bold">Theo dạng câu hỏi</h2>
              <Bars rows={data.question_types} labels={questionTypes} />
            </section>
            <section className="panel p-6">
              <h2 className="mb-5 text-lg font-bold">Theo chủ đề</h2>
              <Bars rows={data.topics} labels={topics} />
            </section>
          </div>
          <p className="text-xs leading-6 text-stone-500">
            {disclaimer} Các tỷ lệ dựa trên câu hỏi thật trong những phiên đã
            nộp, không dùng AI để suy đoán kết quả.
          </p>
        </div>
      ) : (
        !error && (
          <EmptyState
            title="Một bài đọc hôm nay, một bước tiến ngày mai"
            description="Nộp bài Reading đầu tiên để xem điểm, độ chính xác theo dạng câu và gợi ý luyện tập."
          >
            <Button asChild>
              <Link href="/reading">Bắt đầu luyện đọc</Link>
            </Button>
          </EmptyState>
        )
      )}
    </>
  );
}
function Stat({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="panel p-5">
      <p className="text-xs font-semibold text-stone-500">{label}</p>
      <p className="mt-4 text-3xl font-bold text-teal-800">{value}</p>
      <p className="mt-2 text-xs leading-6 text-stone-400">{note}</p>
    </div>
  );
}
function Bars({
  rows,
  labels,
}: {
  rows: Breakdown[];
  labels: Record<string, string>;
}) {
  return (
    <div className="space-y-5">
      {rows.map((row) => (
        <div key={row.key}>
          <div className="mb-2 flex justify-between gap-3 text-xs">
            <span className="font-semibold">{labels[row.key] || row.key}</span>
            <span className="text-stone-500">
              {row.correct}/{row.total} · {row.accuracy}%
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-stone-100">
            <div
              className="h-full rounded-full bg-teal-600"
              style={{ width: `${row.accuracy}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
