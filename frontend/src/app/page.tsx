"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  ChartNoAxesCombined,
  Check,
  PenLine,
  Mic,
  BookOpenText,
  Sparkles,
  Target,
} from "lucide-react";
import { PracticeCards } from "@/features/writing/practice-cards";
import { useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { score } from "@/lib/utils";
import type { Progress } from "@/types";

export default function Home() {
  const { user } = useAuth();
  const [progress, setProgress] = useState<Progress | null>(null);
  useEffect(() => {
    if (user)
      api<Progress>("/progress/summary")
        .then(setProgress)
        .catch(() => {});
  }, [user]);
  return (
    <div className="space-y-10">
      <section className="grid gap-8 overflow-hidden rounded-3xl border border-stone-200 bg-[#edf3ed] p-7 sm:p-10 lg:grid-cols-[1.5fr_1fr] lg:p-12">
        <div>
          <p className="eyebrow mb-6 flex items-center gap-2">
            <span className="size-1.5 rounded-full bg-teal-600" />
            Dành cho hành trình chinh phục VSTEP
          </p>
          <h1 className="max-w-2xl text-4xl font-bold leading-[1.18] tracking-tight sm:text-5xl">
            Mỗi lần luyện,
            <br />
            <span className="text-teal-800">một bước tiến.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-7 text-stone-600 sm:text-base">
            Luyện Reading, Writing và Speaking có định hướng. Nhận phản hồi chi
            tiết từ AI, hiểu lỗi sai và tự tin hơn mỗi ngày.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Button asChild size="lg">
              <Link href="/practice">
                Bắt đầu luyện viết
                <ArrowRight />
              </Link>
            </Button>
            <span className="flex items-center gap-2 text-xs text-stone-500">
              <Check size={15} className="text-teal-700" />
              Writing · Speaking · Reading
            </span>
          </div>
        </div>
        <div className="relative hidden items-center justify-center lg:flex">
          <div className="w-full max-w-sm rotate-2 rounded-2xl border border-white bg-white/85 p-7 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-xs font-semibold text-teal-800">
                <PenLine size={15} />
                NHẬT KÝ LUYỆN VIẾT
              </span>
              <span className="text-xs text-stone-400">VSTEP.3–5</span>
            </div>
            <div className="my-6 h-px bg-stone-200" />
            <p className="font-serif text-2xl italic leading-relaxed text-stone-600">
              “Great writing starts
              <br />
              with a little practice.”
            </p>
            <div className="mt-6 space-y-2.5">
              <div className="h-1.5 w-full rounded bg-stone-100" />
              <div className="h-1.5 w-5/6 rounded bg-stone-100" />
              <div className="h-1.5 w-3/5 rounded bg-stone-100" />
            </div>
            <div className="mt-7 flex items-center gap-2 rounded-lg bg-teal-50 p-3 text-xs text-teal-800">
              <Sparkles size={15} />
              Viết · Nhận phản hồi · Cải thiện
            </div>
          </div>
        </div>
      </section>
      <section>
        <div className="mb-5 flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow mb-2">Chọn nhịp luyện tập của bạn</p>
            <h2 className="text-2xl font-bold tracking-tight">
              Bạn muốn luyện kỹ năng nào?
            </h2>
          </div>
          <Link
            href="/practice"
            className="hidden items-center gap-1 text-sm font-medium text-teal-800 sm:flex"
          >
            Khám phá
            <ArrowUpRight size={16} />
          </Link>
        </div>
        <div className="mb-6 grid gap-5 md:grid-cols-3">
          <div className="panel p-6">
            <PenLine className="mb-4 text-teal-700" />
            <h3 className="text-xl font-bold">Writing</h3>
            <p className="mt-2 text-sm leading-6 text-stone-500">
              Viết rõ ý. Hiểu từng lỗi. Hoàn thiện bài viết.
            </p>
            <div className="mt-5 flex flex-wrap gap-4 text-sm font-semibold text-teal-800">
              <Link href="/practice">Thi thử →</Link>
              <Link href="/practice/task-1">Task 1</Link>
              <Link href="/practice/task-2">Task 2</Link>
            </div>
          </div>
          <div className="panel border-teal-200 bg-teal-50/50 p-6">
            <Mic className="mb-4 text-teal-700" />
            <h3 className="text-xl font-bold">Speaking</h3>
            <p className="mt-2 text-sm leading-6 text-stone-500">
              Nói tự nhiên. Nghe lại bản ghi. Cải thiện từng câu.
            </p>
            <div className="mt-5 flex flex-wrap gap-4 text-sm font-semibold text-teal-800">
              <Link href="/speaking">Thi thử →</Link>
              <Link href="/speaking?mode=PART1">Part 1</Link>
              <Link href="/speaking?mode=PART2">Part 2</Link>
              <Link href="/speaking?mode=PART3">Part 3</Link>
            </div>
          </div>
          <div className="panel p-6">
            <BookOpenText className="mb-4 text-teal-700" />
            <h3 className="text-xl font-bold">Reading</h3>
            <p className="mt-2 text-sm leading-6 text-stone-500">
              Luyện đọc hiểu theo format VSTEP với 4 passages, câu hỏi trắc
              nghiệm và giải thích chi tiết.
            </p>
            <div className="mt-5 flex flex-wrap gap-4 text-sm font-semibold text-teal-800">
              <Link href="/reading">Thi thử →</Link>
              <Link href="/reading?mode=PASSAGE_PRACTICE">Luyện passage</Link>
              <Link href="/reading?mode=QUESTION_TYPE_PRACTICE">
                Theo dạng câu
              </Link>
            </div>
          </div>
        </div>
        <p className="eyebrow mb-4">Tiếp tục luyện Writing</p>
        <PracticeCards />
      </section>
      <section className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <div className="panel p-7">
          <div className="flex items-center justify-between">
            <h2 className="font-bold">
              Một vòng luyện tập, nhiều điều học được
            </h2>
            <Target size={19} className="text-teal-600" />
          </div>
          <div className="mt-7 grid gap-6 sm:grid-cols-3">
            {[
              [
                "01",
                "Viết tập trung",
                "Đề rõ ràng, bộ đếm từ và tự động lưu bài.",
              ],
              ["02", "Hiểu bài viết", "Bốn tiêu chí cùng 3 ưu tiên cải thiện."],
              [
                "03",
                "Tiến bộ từng ngày",
                "Chữa từng câu và theo dõi điểm qua các lần luyện.",
              ],
            ].map(([n, title, text]) => (
              <div key={n}>
                <span className="text-xs font-bold text-teal-700">{n} /</span>
                <h3 className="mb-2 mt-3 text-sm font-semibold">{title}</h3>
                <p className="text-xs leading-6 text-stone-500">{text}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="panel p-7">
          <div className="flex items-center justify-between">
            <h2 className="font-bold">Hành trình của bạn</h2>
            <ChartNoAxesCombined size={19} className="text-teal-600" />
          </div>
          {user && progress ? (
            <>
              <div className="my-6 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-3xl font-bold">
                    {progress.graded_attempts}
                  </p>
                  <p className="mt-2 text-xs text-stone-500">
                    Bài đã được chấm
                  </p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-teal-800">
                    {score(progress.average_task_score)}
                  </p>
                  <p className="mt-2 text-xs text-stone-500">
                    Điểm Task trung bình
                  </p>
                </div>
              </div>
              <Link
                href="/progress"
                className="flex items-center gap-2 text-sm font-semibold text-teal-800"
              >
                Xem tiến độ
                <ArrowRight size={15} />
              </Link>
            </>
          ) : (
            <>
              <p className="my-5 text-sm leading-7 text-stone-500">
                Mỗi lần luyện đều đáng ghi nhận. Lưu bài viết và nhìn lại sự
                tiến bộ của chính mình.
              </p>
              <Button asChild variant="outline" size="sm">
                <Link href={user ? "/progress" : "/register"}>
                  {user ? "Xem tiến độ" : "Tạo tài khoản miễn phí"}
                  <ArrowRight />
                </Link>
              </Button>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
