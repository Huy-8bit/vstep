"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { api } from "@/services/api";
import { PronunciationHistory } from "./pronunciation-coach";
import { SkillSwitch } from "./skill-switch";
import { modes, topics, duration, scoreText, type SpeakingMode } from "./types";
type HistoryItem = {
  id: string;
  mode: SpeakingMode;
  status: string;
  started_at: string;
  parts: number[];
  topics: string[];
  duration_seconds: number;
  score: number | null;
  level: string | null;
};
export function SpeakingHistory() {
  return (
    <RequireAuth>
      <History />
    </RequireAuth>
  );
}
function History() {
  const [data, setData] = useState<{
    total: number;
    items: HistoryItem[];
  } | null>(null);
  const [mode, setMode] = useState("");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      setData(
        await api(
          `/speaking/history?offset=${offset}&limit=15${mode ? `&mode=${mode}` : ""}`,
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [mode, offset]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <>
      <SkillSwitch section="history" active="speaking" />
      <div className="mb-7">
        <PronunciationHistory />
      </div>
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Nhìn lại để tiến bộ</p>
          <h1 className="mt-2 text-3xl font-bold">Lịch sử Speaking</h1>
          <p className="mt-3 text-sm text-stone-500">
            Bản ghi, phản hồi và những phiên bạn đang luyện dở.
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
            {Object.entries(modes).map(([value, item]) => (
              <option key={value} value={value}>
                {item.title}
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
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="border-b border-stone-100 bg-stone-50 text-xs text-stone-500">
                <tr>
                  {[
                    "Ngày luyện",
                    "Chế độ / Part",
                    "Chủ đề",
                    "Audio",
                    "Điểm AI",
                    "Mức AI ước tính",
                    "",
                  ].map((label, i) => (
                    <th key={i} className="px-5 py-4 font-medium">
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-stone-100 last:border-0"
                  >
                    <td className="px-5 py-5 text-stone-500">
                      {new Date(item.started_at).toLocaleDateString("vi-VN")}
                      <p className="mt-1 text-xs">
                        {new Date(item.started_at).toLocaleTimeString("vi-VN", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </td>
                    <td className="px-5 py-5 font-semibold">
                      {modes[item.mode].title}
                      <p className="mt-1 text-xs font-normal text-stone-500">
                        Part {item.parts.join(" · ")}
                      </p>
                    </td>
                    <td className="max-w-52 px-5 py-5 text-xs leading-6 text-stone-600">
                      {item.topics.map((t) => topics[t] || t).join(" · ")}
                    </td>
                    <td className="px-5 py-5 tabular-nums">
                      {duration(item.duration_seconds)}
                    </td>
                    <td className="px-5 py-5 font-bold text-teal-800">
                      {scoreText(item.score)}
                    </td>
                    <td className="px-5 py-5 text-xs text-stone-500">
                      {item.level ||
                        (item.status === "IN_PROGRESS"
                          ? "Đang luyện"
                          : "Chưa chấm")}
                    </td>
                    <td className="px-5 py-5">
                      <Link
                        href={`/speaking/${item.status === "IN_PROGRESS" ? "exam" : "result"}/${item.id}`}
                        className="whitespace-nowrap font-semibold text-teal-800"
                      >
                        {item.status === "IN_PROGRESS"
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
          <div className="mt-5 flex items-center justify-between gap-4 text-xs text-stone-500">
            <span>
              {offset + 1}–{Math.min(offset + 15, data.total)} / {data.total}{" "}
              phiên
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={!offset}
                onClick={() => setOffset(Math.max(0, offset - 15))}
              >
                Trước
              </Button>
              <Button
                size="sm"
                variant="outline"
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
            title="Bắt đầu nhật ký luyện nói của bạn"
            description="Mỗi bản ghi là một cơ hội để nghe lại và hiểu cách bạn đang tiến bộ."
          >
            <Button asChild>
              <Link href="/speaking">Luyện nói ngay</Link>
            </Button>
          </EmptyState>
        )
      )}
    </>
  );
}
