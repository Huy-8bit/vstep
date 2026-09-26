"use client";
import Link from "next/link";
import { ArrowRight, Check, PenLine, Sparkles, Mic, BookOpenText, ArrowUpRight } from "lucide-react";
import { useAuth } from "@/features/auth/auth-provider";
import { HomeDashboard } from "@/features/home/dashboard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Caption } from "@/components/ui/typography";

const LANDING_SKILLS = [
  {
    icon: PenLine,
    title: "Writing",
    description: "Viết rõ ý. Hiểu từng lỗi. Hoàn thiện bài viết.",
    href: "/practice",
  },
  {
    icon: Mic,
    title: "Speaking",
    description: "Nói tự nhiên. Nghe lại bản ghi. Cải thiện từng câu.",
    href: "/speaking",
  },
  {
    icon: BookOpenText,
    title: "Reading",
    description: "Luyện đọc hiểu 4 passage với giải thích chi tiết theo format VSTEP.",
    href: "/reading",
  },
];

export default function Home() {
  const { user, loading } = useAuth();
  if (loading) return <div className="h-96" />;
  if (user) return <HomeDashboard />;
  return (
    <div className="space-y-10">
    <section className="grid gap-8 overflow-hidden rounded-3xl border border-stone-200 bg-[#edf3ed] p-7 sm:p-10 lg:grid-cols-[1.5fr_1fr] lg:p-12">
      <div className="animate-fade-in-up">
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
          Luyện Reading, Writing và Speaking có định hướng. Nhận phản hồi chi tiết
          từ AI, hiểu lỗi sai và tự tin hơn mỗi ngày.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Button asChild size="lg">
            <Link href="/register">
              Bắt đầu miễn phí
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
        <div className="w-full max-w-sm rotate-2 rounded-2xl border border-white bg-white/85 p-7 shadow-lg">
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
          <Caption>Bên trong VSTEP Practice Platform</Caption>
          <h2 className="mt-2 text-2xl font-bold tracking-tight">Ba kỹ năng, một hành trình</h2>
        </div>
        <Link href="/pricing" className="hidden items-center gap-1 text-sm font-medium text-teal-800 sm:flex">
          Xem bảng giá
          <ArrowUpRight size={16} />
        </Link>
      </div>
      <div className="grid gap-5 md:grid-cols-3">
        {LANDING_SKILLS.map((s) => (
          <Card interactive key={s.title} className="p-6">
            <s.icon className="mb-4 text-teal-700" />
            <h3 className="text-xl font-bold">{s.title}</h3>
            <p className="mt-2 text-sm leading-6 text-stone-500">{s.description}</p>
            <Link href={s.href} className="mt-5 flex items-center gap-1 text-sm font-semibold text-teal-800">
              Thử ngay
              <ArrowRight size={15} />
            </Link>
          </Card>
        ))}
      </div>
    </section>
    </div>
  );
}
