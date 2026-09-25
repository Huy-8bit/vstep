"use client";
import Link from "next/link";
import { ArrowUpRight, Target } from "lucide-react";
import { useLearning } from "./shared";

export function LearningEntry({ skill }: { skill?: string }) {
  return (
    <Link
      href="/learning"
      className="my-5 flex items-center justify-between gap-4 rounded-xl border border-teal-100 bg-teal-50 p-4"
    >
      <div className="flex items-center gap-3">
        <Target size={20} className="shrink-0 text-teal-700" />
        <div>
          <p className="text-sm font-semibold text-teal-950">
            Luyện theo điểm yếu của tôi{skill ? ` · ${skill}` : ""}
          </p>
          <p className="mt-1 text-xs leading-6 text-teal-800">
            Xem lỗi lặp lại, học quy tắc và tạo bài luyện phù hợp.
          </p>
        </div>
      </div>
      <ArrowUpRight size={18} className="shrink-0 text-teal-800" />
    </Link>
  );
}
export function AttemptLearningSignals({
  skill,
  attemptId,
}: {
  skill: string;
  attemptId: string;
}) {
  const { data, error, reload } = useLearning<{
    items: {
      concept_key: string;
      label: string;
      count: number;
      weakness_id: string | null;
    }[];
  }>(`/attempts/${skill}/${attemptId}`);
  return (
    <section className="panel my-6 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-base font-semibold">
          <Target size={18} />
          Học tiếp từ bài này
        </h2>
        <Link href="/learning" className="text-sm text-teal-800 underline">
          Phân tích học tập →
        </Link>
      </div>
      {error ? (
        <button
          className="mt-3 text-sm text-stone-500 underline"
          onClick={reload}
        >
          Chưa tải được nội dung học · thử lại
        </button>
      ) : data?.items.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {data.items.map((i) =>
            i.weakness_id ? (
              <Link
                key={i.concept_key}
                href={`/learning/weaknesses?id=${i.weakness_id}`}
                className="rounded-lg bg-teal-50 px-3 py-2 text-sm text-teal-900"
              >
                {i.label} · {i.count} lần ↗
              </Link>
            ) : null,
          )}
        </div>
      ) : (
        <p className="mt-3 text-sm leading-7 text-stone-500">
          Xem hồ sơ học tập để tổng hợp bằng chứng từ các bài đã chấm và chọn
          nội dung luyện tiếp.
        </p>
      )}
    </section>
  );
}
