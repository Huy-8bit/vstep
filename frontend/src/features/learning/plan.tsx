"use client";
import { useState } from "react";
import Link from "next/link";
import { CalendarDays, Check, LoaderCircle } from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { api, post } from "@/services/api";
import { LearningHeader, LoadError, useLearning } from "./shared";
import type { Plan, PlanItem } from "./types";
export function LearningPlan() {
  return (
    <RequireAuth>
      <PlanView />
    </RequireAuth>
  );
}
function PlanView() {
  const { data, error, reload, setData } = useLearning<Plan | null>(
    "/study-plan/current",
  );
  const [days, setDays] = useState(7);
  const [minutes, setMinutes] = useState(25);
  const [busy, setBusy] = useState("");
  const [actionError, setActionError] = useState("");
  async function create() {
    setBusy("create");
    setActionError("");
    try {
      setData(
        await post<Plan>("/learning/study-plan", {
          duration_days: days,
          daily_minutes: minutes,
        }),
      );
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function update(item: PlanItem, status: string) {
    setBusy(item.id);
    setActionError("");
    try {
      const updated = await api<PlanItem>(
        `/learning/study-plan/items/${item.id}`,
        { method: "PATCH", body: JSON.stringify({ status }) },
      );
      setData((p) =>
        p
          ? {
              ...p,
              items: p.items.map((i) => (i.id === updated.id ? updated : i)),
            }
          : p,
      );
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  const dates = data ? [...new Set(data.items.map((i) => i.date))] : [];
  return (
    <div className="space-y-7">
      <LearningHeader
        title="Kế hoạch học tập"
        description="Lịch học ngắn dựa trên điểm cần ưu tiên và tiến bộ của chính bạn."
      />
      {error && <LoadError message={error} retry={reload} />}
      {actionError && <ErrorNotice message={actionError} />}
      <section className="panel p-6">
        <h2 className="flex items-center gap-2 font-semibold">
          <CalendarDays size={18} />
          Thiết kế nhịp học phù hợp
        </h2>
        <div className="mt-5 flex flex-wrap items-end gap-4">
          <label className="grid gap-2 text-sm">
            Thời gian kế hoạch
            <select
              className="field"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
            >
              {[7, 14, 30].map((n) => (
                <option key={n} value={n}>
                  {n} ngày
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm">
            Thời gian mỗi ngày
            <select
              className="field"
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            >
              {[15, 25, 40].map((n) => (
                <option key={n} value={n}>
                  {n} phút
                </option>
              ))}
            </select>
          </label>
          <Button onClick={create} disabled={!!busy}>
            {busy === "create" && <LoaderCircle className="animate-spin" />}
            {data
              ? "Lập kế hoạch mới từ tiến bộ hiện tại"
              : "Tạo kế hoạch cá nhân"}
          </Button>
        </div>
        <p className="mt-4 text-xs leading-6 text-stone-500">
          Mỗi ngày tập trung một nội dung: học ngắn, luyện và ôn lại trong ngữ
          cảnh mới. Kế hoạch mới lưu kế hoạch cũ vào lịch sử.
        </p>
      </section>
      {data ? (
        <>
          <div className="flex flex-wrap justify-between gap-3">
            <h2 className="text-xl font-semibold">
              Kế hoạch {data.duration_days} ngày
            </h2>
            <p className="text-sm text-stone-500">
              {data.items.filter((i) => i.status === "COMPLETED").length}/
              {data.items.length} hoạt động hoàn thành
            </p>
          </div>
          <div className="space-y-4">
            {dates.map((date, index) => (
              <section className="panel p-5" key={date}>
                <div className="mb-4 flex flex-wrap justify-between gap-2">
                  <h3 className="font-semibold">
                    Ngày {index + 1}{" "}
                    <span className="ml-2 text-sm font-normal text-stone-500">
                      {new Date(date + "T12:00:00").toLocaleDateString("vi-VN")}
                    </span>
                  </h3>
                  <span className="text-xs text-stone-500">
                    {data.items
                      .filter((i) => i.date === date)
                      .reduce((sum, i) => sum + i.estimated_minutes, 0)}{" "}
                    phút
                  </span>
                </div>
                <div className="space-y-3">
                  {data.items
                    .filter((i) => i.date === date)
                    .map((item) => (
                      <div
                        className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-stone-50 p-4"
                        key={item.id}
                      >
                        <div>
                          <p
                            className={`text-sm font-medium ${item.status === "COMPLETED" ? "text-teal-700" : ""}`}
                          >
                            {item.activity_type === "LESSON"
                              ? "Học quy tắc"
                              : item.activity_type === "REVIEW"
                                ? "Ôn lại"
                                : item.activity_type === "TRANSFER"
                                  ? "Áp dụng vào bài mới"
                                  : "Luyện tập"}{" "}
                            · {item.title}
                          </p>
                          <p className="mt-2 text-xs text-stone-500">
                            {item.estimated_minutes} phút
                            {item.activity_type === "PRACTICE"
                              ? ` · ${item.exercise_count} câu`
                              : ""}{" "}
                            · {item.reason_vi}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button asChild variant="outline" size="sm">
                            <Link href={item.url}>Mở hoạt động</Link>
                          </Button>
                          <Button
                            size="sm"
                            variant={
                              item.status === "COMPLETED"
                                ? "secondary"
                                : "outline"
                            }
                            disabled={!!busy}
                            onClick={() =>
                              update(
                                item,
                                item.status === "COMPLETED"
                                  ? "PENDING"
                                  : "COMPLETED",
                              )
                            }
                          >
                            <Check size={14} />
                            {item.status === "COMPLETED"
                              ? "Đã xong"
                              : "Đánh dấu xong"}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={!!busy}
                            onClick={() =>
                              update(
                                item,
                                item.status === "SKIPPED"
                                  ? "PENDING"
                                  : "SKIPPED",
                              )
                            }
                          >
                            {item.status === "SKIPPED" ? "Khôi phục" : "Bỏ qua"}
                          </Button>
                        </div>
                      </div>
                    ))}
                </div>
              </section>
            ))}
          </div>
          <p className="text-xs leading-6 text-stone-500">
            Đánh dấu hoàn thành chỉ theo dõi lịch học. Thành thạo được xác định
            từ kết quả luyện và bằng chứng dùng đúng.
          </p>
        </>
      ) : (
        <div className="panel p-8 text-sm leading-7 text-stone-500">
          Chưa có kế hoạch đang áp dụng. Sau khi có bài đã chấm, hệ thống sẽ
          chọn nội dung học từ bằng chứng của bạn.
        </div>
      )}
    </div>
  );
}
