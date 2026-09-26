"use client";
import Link from "next/link";
import { Sparkles, ArrowRight } from "lucide-react";
import { useAuth } from "@/features/auth/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

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
      className={`relative overflow-hidden rounded-2xl border border-amber-200/70 bg-gradient-to-br from-amber-50 to-amber-100/40 ${compact ? "p-5" : "p-7"}`}
    >
      <Badge variant="premium">
        <Sparkles size={11} />
        Quyền VIP
      </Badge>
      <h2 className="mt-3 text-xl font-bold text-stone-900">{title}</h2>
      <p className="mt-2 max-w-lg text-sm leading-6 text-stone-600">
        Luyện đủ Writing Task 1 & 2, Speaking Part 1–3 và Reading; nhận phản hồi
        AI, luyện phát âm, từ vựng và phân tích học tập.
      </p>
      <Button asChild className="mt-5">
        <Link href="/pricing">
          Xem gói VIP từ 50.000đ
          <ArrowRight size={15} />
        </Link>
      </Button>
    </div>
  );
}
