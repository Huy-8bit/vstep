"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  FileQuestion,
  FolderOpen,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Settings2,
  Users,
  Wallet,
  X,
} from "lucide-react";
import { useAuth } from "@/features/auth/auth-provider";

const items = [
  { href: "/admin", label: "Tổng quan", icon: LayoutDashboard },
  { href: "/admin/users", label: "Người dùng", icon: Users },
  { href: "/admin/subscriptions", label: "Gói VIP", icon: CreditCard },
  { href: "/admin/payments", label: "Thanh toán", icon: Wallet },
  { href: "/admin/questions", label: "Ngân hàng đề", icon: FileQuestion },
  { href: "/admin/exam-sets", label: "Bộ đề", icon: FolderOpen },
  { href: "/admin/reports", label: "Báo cáo", icon: BarChart3 },
  { href: "/admin/ai-usage", label: "Chi phí AI", icon: BarChart3 },
  { href: "/admin/settings", label: "Cấu hình", icon: Settings2 },
];

export function AdminFrame({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState("");
  const current = items
    .filter(
      (item) =>
        pathname === item.href ||
        (item.href !== "/admin" && pathname.startsWith(item.href + "/")),
    )
    .sort((a, b) => b.href.length - a.href.length)[0];
  if (loading)
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="h-8 w-40 animate-pulse rounded bg-slate-200" />
        <div className="mt-10 h-72 animate-pulse rounded-xl bg-slate-100" />
      </div>
    );
  if (!user)
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50">
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold">Đăng nhập quản trị</h1>
          <p className="mt-2 text-sm text-slate-500">
            Dùng tài khoản Admin để tiếp tục.
          </p>
          <Link
            className="mt-5 inline-flex rounded-md bg-teal-800 px-4 py-2 text-sm font-semibold text-white"
            href={"/login?next=" + encodeURIComponent(pathname)}
          >
            Đăng nhập
          </Link>
        </div>
      </div>
    );
  if (user.role !== "ADMIN")
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50">
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
          <h1 className="text-xl font-semibold">Bạn không có quyền quản trị</h1>
          <Link
            className="mt-4 inline-block text-sm text-teal-800 underline"
            href="/"
          >
            Về trang học tập
          </Link>
        </div>
      </div>
    );
  return (
    <div className="min-h-screen bg-[#f7f9fa] text-slate-900 lg:flex">
      {mobileOpen && (
        <button
          className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
          aria-label="Đóng menu quản trị"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside
        className={
          "fixed inset-y-0 left-0 z-50 flex flex-col border-r border-slate-200 bg-white transition-[width,transform] duration-200 lg:sticky lg:top-0 lg:h-screen " +
          (collapsed ? "w-[68px] " : "w-[228px] ") +
          (mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0")
        }
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-100 px-4">
          <Link
            href="/admin"
            className="flex min-w-0 items-center gap-2.5"
            title="VSTEP Admin"
          >
            <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-teal-900 text-white">
              <BookOpen size={17} />
            </span>
            {!collapsed && (
              <span className="truncate text-sm font-bold tracking-tight">
                VSTEP <span className="font-normal text-slate-500">Admin</span>
              </span>
            )}
          </Link>
          <button
            className="rounded-md p-1 text-slate-500 hover:bg-slate-100 lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Đóng"
          >
            <X size={17} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2.5 py-5">
          {!collapsed && (
            <p className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Quản lý
            </p>
          )}
          <nav aria-label="Điều hướng quản trị" className="space-y-0.5">
            {items.map((item) => {
              const Icon = item.icon;
              const selected = current?.href === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? item.label : undefined}
                  aria-current={selected ? "page" : undefined}
                  onClick={() => setMobileOpen(false)}
                  className={
                    "flex h-9 items-center gap-3 rounded-md px-2.5 text-sm transition " +
                    (selected
                      ? "bg-teal-50 font-semibold text-teal-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900")
                  }
                >
                  <Icon size={17} className="shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="space-y-1 border-t border-slate-100 p-2.5">
          <Link
            href="/"
            title="Mở app người học"
            className="flex h-9 items-center gap-3 rounded-md px-2.5 text-sm text-slate-600 hover:bg-slate-50"
          >
            <BookOpen size={17} />
            {!collapsed && "App người học"}
          </Link>
          <button
            title="Đăng xuất"
            className="flex h-9 w-full items-center gap-3 rounded-md px-2.5 text-sm text-slate-600 hover:bg-slate-50"
            onClick={async () => {
              await logout();
              router.push("/");
            }}
          >
            <LogOut size={17} />
            {!collapsed && "Đăng xuất"}
          </button>
          {!collapsed && (
            <p
              className="truncate px-2.5 pt-2 text-xs text-slate-400"
              title={user.email}
            >
              {user.email}
            </p>
          )}
          <button
            className="hidden h-8 w-full items-center justify-center rounded-md text-slate-400 hover:bg-slate-50 lg:flex"
            aria-label={collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <div className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-slate-200 bg-white/95 px-5 backdrop-blur lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <button
              className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100 lg:hidden"
              aria-label="Mở menu quản trị"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={19} />
            </button>
            <span className="truncate text-sm font-semibold text-slate-800">
              {current?.label || "Quản trị"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <form
              className="relative hidden sm:block"
              onSubmit={(event) => {
                event.preventDefault();
                if (search.trim())
                  router.push(
                    "/admin/users?search=" + encodeURIComponent(search.trim()),
                  );
              }}
            >
              <Search
                size={15}
                className="absolute left-3 top-2.5 text-slate-400"
              />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Tìm người dùng..."
                aria-label="Tìm người dùng"
                className="h-9 w-56 rounded-md border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none focus:border-teal-600 focus:bg-white"
              />
            </form>
            <div
              className="flex size-8 items-center justify-center rounded-full bg-teal-100 text-xs font-bold text-teal-900"
              title={user.email}
            >
              {user.email.slice(0, 2).toUpperCase()}
            </div>
          </div>
        </div>
        <main className="mx-auto w-full max-w-[1540px] px-5 py-7 lg:px-8 lg:py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
