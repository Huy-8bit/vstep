"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, FileClock, Plus } from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { api } from "@/services/api";
import { modes, topics } from "@/lib/constants";
import { formatDate, score } from "@/lib/utils";
import type { Attempt, Mode } from "@/types";

function History() {
  const [mode, setMode] = useState("");
  const [page, setPage] = useState(0);
  const [data, setData] = useState<{ items: Attempt[]; total: number } | null>(
    null,
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    api<{ items: Attempt[]; total: number }>(
      `/attempts?limit=15&offset=${page * 15}${mode ? `&mode=${mode}` : ""}`,
    )
      .then((result) => {
        if (active) {
          setData(result);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page, mode, reload]);
  return (
    <>
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Mỗi bài viết đều được ghi lại</p>
          <h1 className="mb-3 mt-3 text-3xl font-bold">Lịch sử luyện tập</h1>
          <p className="text-sm text-stone-500">
            Tiếp tục bài đang viết hoặc xem lại phản hồi để ôn tập.
          </p>
        </div>
        <Button asChild>
          <Link href="/practice">
            <Plus />
            Bài luyện mới
          </Link>
        </Button>
      </div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <p className="mb-5 text-sm">
          <Link href="/vocabulary" className="font-semibold text-teal-700">
            Từ vựng đã lưu & lịch sử ôn →
          </Link>
        </p>
        <div className="flex items-center gap-2 text-sm font-semibold">
          <FileClock size={17} className="text-teal-700" />
          {data?.total ?? 0} bài viết
        </div>
        <div className="flex items-center gap-3">
          <label htmlFor="history-mode" className="text-xs text-stone-500">
            Lọc theo
          </label>
          <select
            id="history-mode"
            className="field w-auto!"
            value={mode}
            onChange={(e) => {
              setMode(e.target.value);
              setPage(0);
              setLoading(true);
            }}
          >
            <option value="">Tất cả chế độ</option>
            {Object.entries(modes).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>
      {error ? (
        <>
          <ErrorNotice message={error} />
          <Button
            variant="outline"
            onClick={() => {
              setLoading(true);
              setReload((r) => r + 1);
            }}
          >
            Thử lại
          </Button>
        </>
      ) : loading ? (
        <Loading />
      ) : data?.items.length ? (
        <>
          <div className="panel overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-stone-200 bg-stone-50 text-xs text-stone-500">
                <tr>
                  {[
                    "Ngày luyện",
                    "Bài viết",
                    "Chủ đề",
                    "Số từ",
                    "Điểm AI ước tính",
                    "",
                  ].map((title, i) => (
                    <th
                      key={i}
                      className="whitespace-nowrap px-5 py-4 font-medium"
                    >
                      {title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((a) => (
                  <tr
                    key={a.id}
                    className="border-b border-stone-100 last:border-0 hover:bg-stone-50/50"
                  >
                    <td className="whitespace-nowrap px-5 py-5 text-xs text-stone-500">
                      {formatDate(a.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-5 py-5">
                      <p className="font-semibold">Task {a.task_type}</p>
                      <p className="mt-1 text-xs text-stone-400">
                        {modes[a.mode as Mode]}
                      </p>
                    </td>
                    <td className="px-5 py-5 text-stone-500">
                      {topics[a.question.topic]}
                    </td>
                    <td className="px-5 py-5 text-stone-500">{a.word_count}</td>
                    <td className="px-5 py-5">
                      {a.grading ? (
                        <span className="rounded-lg bg-teal-50 px-3 py-1.5 font-bold text-teal-800">
                          {score(a.grading.scores.overall)}
                          <span className="text-xs font-normal text-teal-600">
                            {" "}
                            / 10
                          </span>
                        </span>
                      ) : (
                        <span className="text-xs text-stone-400">
                          {a.status === "DRAFT" ? "Đang viết" : "Chưa chấm"}
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-5">
                      <Button asChild size="sm" variant="ghost">
                        <Link
                          href={
                            a.status === "DRAFT"
                              ? `/exam/${a.exam_session_id}`
                              : `/result/${a.id}`
                          }
                        >
                          {a.status === "DRAFT" ? "Viết tiếp" : "Xem bài"}
                          <ArrowRight />
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-5 flex items-center justify-between text-xs text-stone-500">
            <span>
              Trang {page + 1} / {Math.ceil(data.total / 15)}
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={page === 0}
                onClick={() => {
                  setPage((p) => p - 1);
                  setLoading(true);
                }}
              >
                Trang trước
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={(page + 1) * 15 >= data.total}
                onClick={() => {
                  setPage((p) => p + 1);
                  setLoading(true);
                }}
              >
                Trang sau
              </Button>
            </div>
          </div>
        </>
      ) : (
        <EmptyState
          title="Trang đầu của hành trình viết"
          description="Bài viết và phản hồi sẽ được lưu tại đây sau buổi luyện tập đầu tiên của bạn."
        >
          <Button asChild>
            <Link href="/practice">
              Bắt đầu luyện tập
              <ArrowRight />
            </Link>
          </Button>
        </EmptyState>
      )}
    </>
  );
}
export function HistoryView() {
  return (
    <RequireAuth>
      <History />
    </RequireAuth>
  );
}
