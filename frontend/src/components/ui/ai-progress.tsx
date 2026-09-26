"use client";
import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const DEFAULT_STAGES = [
  "Đang gửi bài làm của bạn",
  "Đang đọc và phân tích nội dung",
  "Đang kiểm tra ngữ pháp và từ vựng",
  "Đang tổng hợp phản hồi chi tiết",
];

/**
 * Full-screen staged loading for AI grading. Stages progress on a timer as a general
 * sense of activity — they are not tied to real backend milestones (see docs/ui-design-system.md).
 */
export function AiProgressOverlay({
  stages = DEFAULT_STAGES,
  title = "AI đang chấm bài của bạn",
}: {
  stages?: string[];
  title?: string;
}) {
  const [i, setI] = useState(0);
  useEffect(() => {
    setI(0);
    const timer = setInterval(() => {
      setI((v) => Math.min(v + 1, stages.length - 1));
    }, 2600);
    return () => clearInterval(timer);
  }, [stages]);
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-50 flex items-center justify-center bg-white/85 backdrop-blur-sm animate-fade-in"
    >
      <div className="animate-scale-in mx-4 w-full max-w-sm rounded-2xl border border-stone-200 bg-white p-8 text-center shadow-xl">
        <span className="mx-auto mb-5 flex size-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
          <Sparkles size={26} className="animate-soft-pulse" />
        </span>
        <h2 className="text-lg font-bold text-stone-900">{title}</h2>
        <p className="mt-3 min-h-10 text-sm leading-6 text-stone-500">{stages[i]}</p>
        <div className="mt-6 flex justify-center gap-1.5">
          {stages.map((_, idx) => (
            <span
              key={idx}
              className={cn(
                "h-1.5 w-6 rounded-full transition-colors duration-500",
                idx <= i ? "bg-teal-600" : "bg-stone-100",
              )}
            />
          ))}
        </div>
        <p className="mt-6 text-xs text-stone-400">
          Thường mất khoảng 15–30 giây · đừng tắt trang này.
        </p>
      </div>
    </div>
  );
}
