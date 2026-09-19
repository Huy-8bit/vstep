"use client";
import { LearningEntry } from "@/features/learning/integration";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ChartNoAxesCombined,
  PenLine,
  Target,
  Trophy,
} from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { RequireAuth } from "@/features/auth/auth-provider";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { categories, criteria, errorTypes, modes } from "@/lib/constants";
import { DISCLAIMER, score } from "@/lib/utils";
import { VocabularyProgressPanel } from "@/features/vocabulary/progress";
import type { ErrorStat, Progress } from "@/types";

function ErrorChart({ items, title }: { items: ErrorStat[]; title: string }) {
  const max = Math.max(...items.map((e) => e.count), 1);
  return (
    <section className="panel p-6">
      <h2 className="mb-6 font-bold">{title}</h2>
      {items.length ? (
        <div className="space-y-5">
          {items.slice(0, 5).map((e) => (
            <div key={`${e.category}-${e.subtype}`}>
              <div className="mb-2 flex justify-between gap-3 text-xs">
                <span className="text-stone-500">
                  {errorTypes[e.subtype] ||
                    categories[e.category] ||
                    "Diễn đạt"}
                </span>
                <strong>{e.count} lần</strong>
              </div>
              <div className="h-2 rounded-full bg-stone-100">
                <div
                  className="h-full rounded-full bg-teal-600/70"
                  style={{ width: `${(e.count / max) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-stone-400">
          Chưa có lỗi thuộc nhóm này được ghi nhận.
        </p>
      )}
    </section>
  );
}
function Dashboard() {
  const [data, setData] = useState<Progress | null>(null);
  const [errors, setErrors] = useState<ErrorStat[]>([]);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [mode, setMode] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([
      api<Progress>("/progress/summary"),
      api<ErrorStat[]>("/progress/errors"),
    ])
      .then(([summary, issues]) => {
        if (active) {
          setData(summary);
          setErrors(issues);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [reload]);
  if (error)
    return (
      <>
        <ErrorNotice message={error} />
        <Button onClick={() => setReload((r) => r + 1)}>Thử lại</Button>
      </>
    );
  if (!data) return <Loading />;
  const chart = data.progression
    .filter((p) => !mode || p.mode === mode)
    .map((p, index) => ({
      index: index + 1,
      date: new Date(p.date).toLocaleDateString("vi-VN"),
      FULL_TEST: p.mode === "FULL_TEST" ? p.score : null,
      TASK1: p.mode === "TASK1" ? p.score : null,
      TASK2: p.mode === "TASK2" ? p.score : null,
    }));
  return (
    <div className="space-y-7">
<LearningEntry />
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Nhìn lại để đi xa hơn</p>
          <h1 className="mb-3 mt-3 text-3xl font-bold">Tiến độ của bạn</h1>
          <p className="text-sm text-stone-500">
            Nhận ra điểm mạnh và tập trung vào điều cần cải thiện tiếp theo.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/practice">
            Tiếp tục luyện tập
            <ArrowRight />
          </Link>
        </Button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: "Writing trung bình",
            value: score(data.average_writing_score),
            sub: "Chỉ tính các bài thi đủ hai Task",
            Icon: Trophy,
          },
          {
            label: "Task trung bình",
            value: score(data.average_task_score),
            sub: "Tất cả bài viết đã được chấm",
            Icon: Target,
          },
          {
            label: "Bài viết đã chấm",
            value: data.graded_attempts,
            sub: `${data.completed_full_tests} phiên Writing hoàn chỉnh`,
            Icon: ChartNoAxesCombined,
          },
          {
            label: "Tổng số từ đã viết",
            value: data.total_words.toLocaleString("vi-VN"),
            sub: "Từ các bài viết đã nộp",
            Icon: PenLine,
          },
        ].map(({ Icon, ...card }) => (
          <div key={card.label} className="panel p-5">
            <div className="flex items-center justify-between text-xs text-stone-500">
              {card.label}
              <Icon size={16} className="text-teal-600" />
            </div>
            <p className="my-4 text-3xl font-bold text-teal-900">
              {card.value}
            </p>
            <p className="text-[11px] text-stone-400">{card.sub}</p>
          </div>
        ))}
      </div>
      {data.graded_attempts === 0 ? (
        <EmptyState
          title="Tiến bộ bắt đầu từ bài viết đầu tiên"
          description="Khi bạn có kết quả chấm AI, điểm số, biểu đồ và các lỗi thường gặp sẽ xuất hiện tại đây."
        >
          <Button asChild>
            <Link href="/practice">
              Luyện viết ngay
              <ArrowRight />
            </Link>
          </Button>
        </EmptyState>
      ) : (
        <>
          <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
            <section className="panel p-5 sm:p-7">
              <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                <h2 className="font-bold">Điểm qua các lần luyện</h2>
                <select
                  aria-label="Chế độ hiển thị biểu đồ"
                  className="field w-auto! py-2! text-xs!"
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                >
                  <option value="">Tất cả chế độ</option>
                  {Object.entries(modes).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              {chart.length ? (
                <div
                  className="h-72 w-full"
                  role="img"
                  aria-label="Biểu đồ điểm AI ước tính theo ngày, thang 0 đến 10"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={chart}
                      margin={{ left: -25, right: 12, top: 10 }}
                    >
                      <CartesianGrid
                        strokeDasharray="4 4"
                        vertical={false}
                        stroke="#e7e5e4"
                      />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 11, fill: "#78716c" }}
                        axisLine={false}
                        tickLine={false}
                        dy={8}
                      />
                      <YAxis
                        domain={[0, 10]}
                        ticks={[0, 2, 4, 6, 8, 10]}
                        tick={{ fontSize: 11, fill: "#78716c" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        formatter={(value) =>
                          typeof value === "number" ? value.toFixed(2) : value
                        }
                        contentStyle={{
                          borderRadius: 12,
                          border: "1px solid #e7e5e4",
                          fontSize: 12,
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: 11, paddingTop: 20 }} />
                      {[
                        ["FULL_TEST", "Writing", "#0f766e"],
                        ["TASK1", "Task 1", "#b78a44"],
                        ["TASK2", "Task 2", "#7c83b5"],
                      ]
                        .filter(([key]) => !mode || key === mode)
                        .map(([key, name, color]) => (
                          <Line
                            key={key}
                            type="linear"
                            dataKey={key}
                            name={name}
                            stroke={color}
                            strokeWidth={2.5}
                            dot={{ r: 4, strokeWidth: 2 }}
                            connectNulls
                            isAnimationActive={false}
                          />
                        ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="py-24 text-center text-sm text-stone-400">
                  Chưa có điểm cho chế độ này.
                </p>
              )}
              <p className="mt-3 text-[11px] leading-5 text-stone-400">
                Tối đa 60 kết quả gần nhất. Điểm Writing dùng trọng số 1:2; điểm
                luyện Task hiển thị riêng.
              </p>
            </section>
            <section className="panel p-7">
              <h2 className="mb-6 font-bold">Trung bình theo tiêu chí</h2>
              <div className="space-y-6">
                {Object.entries(criteria).map(([key, name]) => (
                  <div key={key}>
                    <div className="mb-3 flex justify-between text-sm">
                      <span className="text-stone-500">{name}</span>
                      <strong>{score(data.criteria[key])}</strong>
                    </div>
                    <div className="h-2 rounded-full bg-stone-100">
                      <div
                        className="h-full rounded-full bg-teal-600"
                        style={{ width: `${(data.criteria[key] || 0) * 10}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-6 text-xs leading-6 text-stone-400">
                Tính trên tất cả Task đã chấm, mỗi Task có cùng trọng số trong
                thống kê tiêu chí.
              </p>
            </section>
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            <ErrorChart
              title="Lỗi ngữ pháp thường gặp"
              items={errors.filter((e) =>
                [
                  "grammar",
                  "sentence_structure",
                  "punctuation",
                  "spelling",
                ].includes(e.category),
              )}
            />
            <ErrorChart
              title="Điểm cần cải thiện về từ vựng"
              items={errors.filter((e) =>
                [
                  "vocabulary",
                  "word_choice",
                  "collocation",
                  "register",
                ].includes(e.category),
              )}
            />
          </div>
        </>
      )}
      <VocabularyProgressPanel />
      <p className="text-xs leading-6 text-stone-400">{DISCLAIMER}</p>
    </div>
  );
}
export function ProgressView() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}
