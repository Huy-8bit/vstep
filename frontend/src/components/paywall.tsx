"use client";
import Link from "next/link";
import { useAuth } from "@/features/auth/auth-provider";

export function Paywall({
  title = "Mở toàn bộ luyện tập VSTEP",
  compact = false,
}: {
  title?: string;
  compact?: boolean;
}) {
  const { user } = useAuth();
  if (user?.role === "ADMIN" || user?.access?.tier === "VIP") return null;
  return (
    <div
      className={`rounded-2xl border border-amber-200 bg-amber-50 ${compact ? "p-5" : "p-7"}`}
    >
      <p className="text-xs font-bold uppercase tracking-wider text-amber-800">
        Quyền VIP
      </p>
      <h2 className="mt-2 text-xl font-bold text-stone-900">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-stone-600">
        Luyện đủ Writing Task 1 & 2, Speaking Part 1–3 và Reading; nhận phản hồi
        AI, luyện phát âm, từ vựng và phân tích học tập.
      </p>
      <Link
        href="/pricing"
        className="mt-5 inline-flex rounded-xl bg-teal-800 px-5 py-3 text-sm font-semibold text-white hover:bg-teal-900"
      >
        Xem gói VIP từ 50.000đ →
      </Link>
    </div>
  );
}
