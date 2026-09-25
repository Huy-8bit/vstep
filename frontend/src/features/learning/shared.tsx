"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Target, TrendingUp } from "lucide-react";
import { api } from "@/services/api";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { statusLabels, trends, type Weakness } from "./types";

export function useLearning<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion((v) => v + 1), []);
  useEffect(() => {
    let active = true;
    api<T>(`/learning${path}`)
      .then((value) => {
        if (active) {
          setData(value);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [path, version]);
  return { data, error, reload, setData };
}
export function LearningHeader({
  title = "Phân tích học tập",
  description = "Hiểu điều cần học tiếp theo, từ chính những bài bạn đã làm.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
      <div>
        <p className="eyebrow mb-2">HỌC TỪ BÀI LÀM CỦA BẠN</p>
        <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-500">
          {description}
        </p>
      </div>
      <div className="flex gap-2">
        <Button asChild variant="outline">
          <Link href="/learning">
            <Target className="size-4" />
            Phân tích
          </Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/learning/plan">
            <BookOpen className="size-4" />
            Kế hoạch học
          </Link>
        </Button>
      </div>
    </div>
  );
}
export function WeaknessCard({ item: w }: { item: Weakness }) {
  return (
    <article className="panel flex flex-col p-5">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="rounded-md bg-teal-50 px-2 py-1 text-xs font-medium text-teal-900">
          {w.stats.skills.join(" + ")}
        </span>
        <span className="text-xs text-stone-500">
          {statusLabels[w.status] || w.status}
        </span>
      </div>
      <h3 className="text-lg font-semibold">{w.display_name_vi}</h3>
      <p className="mt-2 text-sm text-stone-600">
        {w.stats.accuracy !== null
          ? `${w.stats.accuracy}% đúng / ${w.stats.question_count} câu`
          : `${w.occurrence_count} lần trong ${w.affected_attempt_count} bài`}
      </p>
      <p className="mt-3 flex items-center gap-2 text-xs text-stone-500">
        <TrendingUp size={14} />
        {trends[w.trend]}
      </p>
      <p className="mt-2 text-xs text-stone-400">
        Mức bằng chứng: {w.stats.confidence_label}
      </p>
      <Button asChild className="mt-5 w-full" variant="outline">
        <Link href={`/learning/weaknesses?id=${w.id}`}>
          Học và luyện điểm này
          <ArrowUpRight size={16} />
        </Link>
      </Button>
    </article>
  );
}
export function WeaknessGrid({ items }: { items: Weakness[] }) {
  return items.length ? (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((w) => (
        <WeaknessCard key={w.id} item={w} />
      ))}
    </div>
  ) : (
    <div className="panel p-8 text-sm leading-7 text-stone-500">
      Chưa có điểm cần ưu tiên trong nhóm này. Hoàn thành thêm bài luyện để có
      bằng chứng rõ hơn.
    </div>
  );
}
export function LoadError({
  message,
  retry,
}: {
  message: string;
  retry: () => void;
}) {
  return (
    <div className="space-y-3">
      <ErrorNotice message={message} />
      <Button variant="outline" onClick={retry}>
        Thử tải lại
      </Button>
    </div>
  );
}
