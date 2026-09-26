"use client";
import { LearningEntry } from "@/features/learning/integration";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, FileClock, Plus } from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Caption, PageTitle, Body } from "@/components/ui/typography";
import { StaggerContainer, StaggerItem } from "@/components/ui/motion";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { LibraryOrigin } from "@/features/library/practice-link";
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
      <LearningEntry />
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <Caption>Mỗi bài viết đều được ghi lại</Caption>
          <PageTitle className="mb-3 mt-2">Lịch sử luyện tập</PageTitle>
          <Body>Tiếp tục bài đang viết hoặc xem lại phản hồi để ôn tập.</Body>
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
          <StaggerContainer className="space-y-3">
            {data.items.map((a) => (
              <StaggerItem key={a.id}>
                <Card interactive className="flex flex-wrap items-center gap-4 p-5">
                  <div className="flex min-w-40 flex-1 items-center gap-4">
                    {a.grading ? (
                      <span className="flex size-12 shrink-0 flex-col items-center justify-center rounded-xl bg-teal-50 text-sm font-bold text-teal-800">
                        {score(a.grading.scores.overall)}
                        <span className="text-[9px] font-medium text-teal-500">/ 10</span>
                      </span>
                    ) : (
                      <span className="flex h-12 shrink-0 items-center justify-center whitespace-nowrap rounded-xl bg-stone-100 px-3 text-xs font-medium text-stone-500">
                        {a.status === "DRAFT" ? "Đang viết" : "Chưa chấm"}
                      </span>
                    )}
                    <div className="min-w-0">
                      <p className="font-semibold">
                        {a.mode === "FULL_TEST"
                          ? `Task ${a.task_type} · ${modes[a.mode as Mode]}`
                          : modes[a.mode as Mode]}
                      </p>
                      <p className="mt-1 truncate text-xs text-stone-500">
                        {topics[a.question.topic] || a.question.topic}
                        <LibraryOrigin value={a.question} />
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-5 text-xs text-stone-400">
                    <span>{a.word_count} từ</span>
                    <span className="hidden sm:inline">{formatDate(a.created_at)}</span>
                  </div>
                  <Button asChild size="sm" variant="ghost">
                    <Link
                      href={
                        a.status === "DRAFT"
                          ? `/exam?id=${a.exam_session_id}`
                          : `/result?id=${a.id}`
                      }
                    >
                      {a.status === "DRAFT" ? "Viết tiếp" : "Xem bài"}
                      <ArrowRight />
                    </Link>
                  </Button>
                </Card>
              </StaggerItem>
            ))}
          </StaggerContainer>
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
