"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/features/auth/auth-provider";
import { SkillSwitch } from "@/features/speaking/skill-switch";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { LibraryOrigin } from "@/features/library/practice-link";
import type { LibraryMetadata } from "@/features/library/types";
import { api } from "@/services/api";
import { modes, topics, duration, type ReadingMode } from "./types";
type Item = LibraryMetadata & {
  id: string;
  mode: ReadingMode;
  topic: string;
  status: string;
  started_at: string;
  question_count: number;
  correct_count: number | null;
  accuracy: number | null;
  score: number | null;
  duration_seconds: number | null;
};
export function ReadingHistory() {
  return (
    <RequireAuth>
      <History />
    </RequireAuth>
  );
}
function History() {
  const [data, setData] = useState<{ total: number; items: Item[] } | null>(
    null,
  );
  const [mode, setMode] = useState("");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(
        await api(
          `/reading/history?offset=${offset}&limit=15${mode ? `&mode=${mode}` : ""}`,
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [offset, mode]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <>
      <SkillSwitch section="history" active="reading" />
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Hành trình đọc hiểu</p>
          <h1 className="mt-2 text-3xl font-bold">Lịch sử Reading</h1>
          <p className="mt-3 text-sm text-stone-500">
            Tiếp tục bài đang làm hoặc nhìn lại đáp án cùng lời giải.
          </p>
        </div>
        <label className="text-xs font-semibold">
          Chế độ
          <select
            className="field mt-2"
            value={mode}
            onChange={(e) => {
              setMode(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">Tất cả chế độ</option>
            {Object.entries(modes).map(([key, m]) => (
              <option key={key} value={key}>
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
      ) : data?.items.length ? (
        <>
          <div className="panel overflow-x-auto">
            <table className="w-full min-w-[880px] text-left text-sm">
              <thead className="border-b border-stone-100 bg-stone-50 text-xs text-stone-500">
                <tr>
                  {[
                    "Ngày luyện",
                    "Chế độ",
                    "Chủ đề",
                    "Số câu đúng",
                    "Điểm luyện tập",
                    "Thời gian",
                    "",
                  ].map((title, i) => (
                    <th key={i} className="px-5 py-4 font-medium">
                      {title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-stone-100 last:border-0"
                  >
                    <td className="px-5 py-5 text-stone-500">
                      {new Date(row.started_at).toLocaleDateString("vi-VN")}
                      <p className="mt-1 text-xs">
                        {new Date(row.started_at).toLocaleTimeString("vi-VN", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </td>
                    <td className="px-5 py-5 font-semibold">
                      {modes[row.mode].title}
                      <LibraryOrigin value={row} />
                      <p className="mt-1 text-xs font-normal text-stone-400">
                        {row.status === "IN_PROGRESS"
                          ? "Đang làm"
                          : row.status === "EXPIRED"
                            ? "Nộp khi hết giờ"
                            : "Đã nộp"}
                      </p>
                    </td>
                    <td className="px-5 py-5 text-xs leading-6">
                      <p className="text-stone-500">
                        {row.topic === "random"
                          ? "Nhiều chủ đề"
                          : topics[row.topic] || row.topic}
                      </p>
                    </td>
                    <td className="px-5 py-5">
                      {row.correct_count ?? "—"} / {row.question_count}
                    </td>
                    <td className="px-5 py-5 font-bold text-teal-800">
                      {row.score?.toFixed(2) ?? "—"}
                      <p className="mt-1 text-xs font-normal text-stone-500">
                        {row.accuracy !== null
                          ? `${row.accuracy}%`
                          : "Chưa nộp"}
                      </p>
                    </td>
                    <td className="px-5 py-5 tabular-nums">
                      {row.duration_seconds !== null
                        ? duration(row.duration_seconds)
                        : "—"}
                    </td>
                    <td className="px-5 py-5">
                      <Link
                        className="whitespace-nowrap font-semibold text-teal-800"
                        href={`/reading/${row.status === "IN_PROGRESS" ? "exam" : "result"}/${row.id}`}
                      >
                        {row.status === "IN_PROGRESS"
                          ? "Tiếp tục"
                          : "Xem kết quả"}{" "}
                        →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-5 flex justify-between gap-3 text-xs text-stone-500">
            <span>
              {offset + 1}–{Math.min(data.total, offset + 15)} / {data.total}{" "}
              phiên
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!offset}
                onClick={() => setOffset(Math.max(0, offset - 15))}
              >
                Trước
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + 15 >= data.total}
                onClick={() => setOffset(offset + 15)}
              >
                Sau
              </Button>
            </div>
          </div>
        </>
      ) : (
        !error && (
          <EmptyState
            title="Bắt đầu trang đầu tiên của hành trình"
            description="Hoàn thành một bài Reading để lưu điểm, đáp án và những điều bạn học được."
          >
            <Button asChild>
              <Link href="/reading">Luyện Reading</Link>
            </Button>
          </EmptyState>
        )
      )}
    </>
  );
}
