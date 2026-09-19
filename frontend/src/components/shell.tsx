"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, ArrowUpRight, LogOut } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { cn } from "@/lib/utils";

export function Brand() {
  return (
    <Link
      href="/"
      className="flex items-center gap-2.5"
      aria-label="VSTEP Practice Platform - Trang chủ"
    >
      <span className="flex size-9 items-center justify-center rounded-xl bg-teal-800 text-white">
        <BookOpen size={19} />
      </span>
      <span className="text-base font-bold tracking-tight">
        VSTEP{" "}
        <span className="font-normal text-stone-500">Practice Platform</span>
      </span>
    </Link>
  );
}
export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  if (
    pathname.startsWith("/exam/") ||
    pathname.startsWith("/speaking/exam/") ||
    pathname.startsWith("/reading/exam/")
  )
    return <>{children}</>;
  return (
    <>
      <header className="sticky top-0 z-30 border-b border-stone-200 bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Brand />
          <nav
            className="order-3 flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto"
            aria-label="Điều hướng chính"
          >
            {[
              ["/", "Trang chủ"],
              ["/practice", "Writing"],
              ["/speaking", "Speaking"],
              ["/reading", "Reading"],
              ["/my-questions", "Đề của tôi"],
              ["/learning", "Phân tích học tập"],
              ["/vocabulary", "Từ vựng"],
              ["/history", "Lịch sử"],
              ["/progress", "Tiến độ"],
              ["/settings", "Cài đặt"],
              ...(user?.is_ai_admin
                ? [["/internal/ai-costs", "Chi phí AI"]]
                : []),
            ].map(([href, label]) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap",
                  (href === "/" ? pathname === "/" : pathname.startsWith(href))
                    ? "bg-teal-50 text-teal-900"
                    : "text-stone-500 hover:bg-stone-50 hover:text-stone-900",
                )}
              >
                {label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <span
                  title={user.email}
                  className="hidden max-w-24 truncate text-xs text-stone-500 lg:block"
                >
                  {user.email}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  title="Đăng xuất"
                  aria-label="Đăng xuất"
                  onClick={async () => {
                    try {
                      await logout();
                      router.push("/");
                    } catch (e) {
                      setError((e as Error).message);
                    }
                  }}
                >
                  <LogOut />
                </Button>
              </>
            ) : (
              <Button asChild size="sm" variant="outline">
                <Link href="/login">
                  {loading ? "Tài khoản" : "Đăng nhập"}
                  <ArrowUpRight />
                </Link>
              </Button>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto min-h-[calc(100vh-180px)] max-w-7xl px-5 py-8 sm:px-8 sm:py-10">
        {error && <ErrorNotice message={error} />}
        {children}
      </main>
      <footer className="mx-auto flex max-w-7xl flex-wrap justify-between gap-3 border-t border-stone-200 px-5 py-6 text-xs text-stone-500 sm:px-8">
        <span>VSTEP Practice Platform · Luyện đọc, viết và nói mỗi ngày.</span>
        <span>Công cụ luyện tập độc lập · Điểm AI mang tính tham khảo.</span>
      </footer>
    </>
  );
}
