"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BookOpen,
  Home,
  NotebookPen,
  LineChart,
  History,
  CircleUserRound,
  ShieldCheck,
  LogOut,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, initials } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ErrorNotice } from "@/components/feedback";
import { cn } from "@/lib/utils";
import { AdminFrame } from "@/features/admin/admin-frame";

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link
      href="/"
      className="flex items-center gap-2.5"
      aria-label="VSTEP Practice Platform - Trang chủ"
    >
      <span className="flex size-9 items-center justify-center rounded-xl bg-teal-800 text-white shadow-sm">
        <BookOpen size={19} />
      </span>
      {!compact && (
        <span className="text-base font-bold tracking-tight">
          VSTEP{" "}
          <span className="hidden font-normal text-stone-500 sm:inline">
            Practice Platform
          </span>
        </span>
      )}
    </Link>
  );
}

const DESKTOP_NAV = [
  ["/", "Trang chủ", (p: string) => p === "/"],
  ["/practice", "Luyện tập", (p: string) => ["/practice", "/speaking", "/reading", "/exam"].some((x) => p.startsWith(x))],
  ["/learning", "Phân tích học tập", (p: string) => p.startsWith("/learning")],
  ["/vocabulary", "Từ vựng", (p: string) => p.startsWith("/vocabulary")],
  ["/history", "Lịch sử", (p: string) => p.startsWith("/history")],
  ["/progress", "Tiến độ", (p: string) => p.startsWith("/progress")],
] as const;

const MOBILE_NAV = [
  ["/", "Trang chủ", Home, (p: string) => p === "/"],
  ["/practice", "Luyện tập", NotebookPen, (p: string) => ["/practice", "/speaking", "/reading", "/exam"].some((x) => p.startsWith(x))],
  ["/learning", "Học tập", LineChart, (p: string) => p.startsWith("/learning")],
  ["/history", "Lịch sử", History, (p: string) => p.startsWith("/history")],
  ["/account", "Tài khoản", CircleUserRound, (p: string) => p.startsWith("/account")],
] as const;

function AccountMenu() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  if (!user) return null;
  const isVip = user.access?.tier === "VIP";
  return (
    <>
      {error && <ErrorNotice message={error} />}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 outline-none transition-colors hover:bg-stone-100 focus-visible:ring-2 focus-visible:ring-teal-600"
            aria-label="Tài khoản"
          >
            <Avatar>
              <AvatarFallback>{initials(user.name || user.email)}</AvatarFallback>
            </Avatar>
            <ChevronDown size={14} className="hidden text-stone-400 sm:block" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel className="flex flex-col gap-1 normal-case">
            <span className="truncate text-sm font-semibold text-stone-900">
              {user.name || user.email.split("@")[0]}
            </span>
            <span className="truncate text-xs font-normal text-stone-400">{user.email}</span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href="/account">
              <CircleUserRound size={16} className="text-stone-400" />
              Tài khoản
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href={isVip ? "/account/subscription" : "/pricing"}>
              <Sparkles size={16} className="text-amber-500" />
              {isVip ? "Gói VIP của bạn" : "Nâng cấp VIP"}
            </Link>
          </DropdownMenuItem>
          {user.role === "ADMIN" && (
            <DropdownMenuItem asChild>
              <Link href="/admin">
                <ShieldCheck size={16} className="text-stone-400" />
                Quản trị
              </Link>
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={async () => {
              try {
                await logout();
                router.push("/");
              } catch (e) {
                setError((e as Error).message);
              }
            }}
            className="text-red-600 focus:bg-red-50 focus:text-red-700"
          >
            <LogOut size={16} />
            Đăng xuất
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  if (pathname.startsWith("/my-questions") && user?.role === "ADMIN")
    return <AdminFrame>{children}</AdminFrame>;
  if (
    pathname.startsWith("/admin") ||
    pathname === "/exam" ||
    pathname === "/speaking/exam" ||
    pathname === "/reading/exam"
  )
    return <>{children}</>;

  const isVip = user?.access?.tier === "VIP";

  return (
    <>
      <header className="sticky top-0 z-30 border-b border-stone-200 bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
          <div className="flex items-center gap-8">
            <Brand />
            <nav
              className="hidden items-center gap-1 md:flex"
              aria-label="Điều hướng chính"
            >
              {DESKTOP_NAV.map(([href, label, match]) => (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "relative rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors",
                    match(pathname)
                      ? "text-teal-900"
                      : "text-stone-500 hover:bg-stone-100 hover:text-stone-900",
                  )}
                >
                  {label}
                  {match(pathname) && (
                    <span className="absolute inset-x-3 -bottom-[15px] h-0.5 rounded-full bg-teal-700" />
                  )}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <Link
                  href={isVip ? "/account/subscription" : "/pricing"}
                  className="hidden sm:block"
                >
                  <Badge variant={isVip ? "premium" : "primary"}>
                    {isVip ? <Sparkles size={11} /> : null}
                    {isVip ? "VIP" : "FREE · Nâng cấp"}
                  </Badge>
                </Link>
                <AccountMenu />
              </>
            ) : loading ? (
              <div className="size-9 animate-pulse rounded-full bg-stone-100" />
            ) : (
              <div className="flex items-center gap-2">
                <Button asChild size="sm" variant="ghost" className="hidden sm:inline-flex">
                  <Link href="/login">Đăng nhập</Link>
                </Button>
                <Button asChild size="sm">
                  <Link href="/register">
                    <span className="sm:hidden">Đăng ký</span>
                    <span className="hidden sm:inline">Đăng ký miễn phí</span>
                  </Link>
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto min-h-[calc(100vh-180px)] max-w-7xl px-5 pb-24 pt-6 sm:px-8 sm:pt-8 md:pb-10">
        {children}
      </main>

      <footer className="mx-auto hidden max-w-7xl flex-wrap justify-between gap-3 border-t border-stone-200 px-5 py-6 text-xs text-stone-500 sm:px-8 md:flex">
        <span>VSTEP Practice Platform · Luyện đọc, viết và nói mỗi ngày.</span>
        <span>Công cụ luyện tập độc lập · Điểm AI mang tính tham khảo.</span>
      </footer>

      {user && (
        <nav
          className="fixed inset-x-0 bottom-0 z-30 flex border-t border-stone-200 bg-white/95 pb-[max(env(safe-area-inset-bottom),8px)] backdrop-blur-md md:hidden"
          aria-label="Điều hướng chính"
        >
          {MOBILE_NAV.map(([href, label, Icon, match]) => {
            const active = match(pathname);
            return (
              <Link
                key={href}
                href={href}
                className="flex flex-1 flex-col items-center gap-1 pt-2.5 pb-1 text-[11px] font-medium"
              >
                <Icon
                  size={21}
                  strokeWidth={active ? 2.4 : 2}
                  className={active ? "text-teal-700" : "text-stone-400"}
                />
                <span className={active ? "text-teal-800" : "text-stone-500"}>{label}</span>
              </Link>
            );
          })}
        </nav>
      )}
    </>
  );
}
