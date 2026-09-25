"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, post } from "@/services/api";
import { useAuth } from "@/features/auth/auth-provider";
import { ErrorNotice } from "@/components/feedback";

type Plan = {
  id: string;
  code: string;
  name: string;
  duration_days: number;
  price_vnd: number;
};
export default function PricingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    api<{ items: Plan[] }>("/subscription/plans")
      .then((data) => setPlans(data.items))
      .catch((e) => setError(e.message));
    if (user) post("/events", { name: "PRICING_VIEWED" }).catch(() => {});
  }, [user]);
  async function choose(code: string) {
    if (!user) {
      router.push(`/login?next=${encodeURIComponent("/pricing")}`);
      return;
    }
    setBusy(code);
    setError("");
    try {
      await post("/payments", { plan_code: code });
      router.push("/account/subscription");
    } catch (e) {
      setError((e as Error).message);
      setBusy("");
    }
  }
  return (
    <div className="space-y-8">
      <div>
        <p className="eyebrow">Học theo nhịp của bạn</p>
        <h1 className="mt-2 text-4xl font-bold">Chọn quyền luyện tập</h1>
        <p className="mt-3 max-w-2xl text-stone-600">
          Bạn có thể thử Writing Task 1 và Speaking Part 1, mỗi kỹ năng một lần.
          VIP mở toàn bộ lộ trình luyện VSTEP.
        </p>
      </div>
      {error && <ErrorNotice message={error} />}
      <div className="grid gap-5 md:grid-cols-4">
        <div className="panel p-6">
          <p className="text-sm font-bold text-stone-500">FREE</p>
          <p className="mt-3 text-3xl font-bold">0đ</p>
          <p className="mt-5 text-sm leading-7 text-stone-600">
            1 lần Writing Task 1<br />1 lần Speaking Part 1<br />
            Có chấm và nhận phản hồi AI
          </p>
          <Link
            href={user ? "/practice/task-1" : "/register"}
            className="mt-8 inline-block text-sm font-semibold text-teal-800"
          >
            Bắt đầu miễn phí →
          </Link>
        </div>
        {plans.map((plan) => (
          <div
            key={plan.code}
            className={`panel p-6 ${plan.duration_days === 30 ? "border-teal-700 bg-teal-50/50" : ""}`}
          >
            {plan.duration_days === 30 && (
              <p className="mb-2 text-xs font-bold uppercase text-teal-800">
                Luyện tập dài hạn
              </p>
            )}
            <p className="text-sm font-bold text-stone-500">{plan.name}</p>
            <p className="mt-3 text-3xl font-bold">
              {new Intl.NumberFormat("vi-VN").format(plan.price_vnd)}đ
            </p>
            <p className="mt-5 text-sm leading-7 text-stone-600">
              Writing Task 1 & 2<br />
              Speaking Part 1, 2, 3<br />
              Reading, AI, phát âm
              <br />
              Từ vựng và phân tích học tập
            </p>
            <button
              onClick={() => choose(plan.code)}
              disabled={!!busy}
              className="mt-8 w-full rounded-xl bg-teal-800 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {busy === plan.code ? "Đang tạo yêu cầu…" : "Chọn gói VIP"}
            </button>
          </div>
        ))}
      </div>
      <p className="text-sm text-stone-500">
        Hiện hỗ trợ xác nhận thanh toán thủ công. Quyền VIP bắt đầu sau khi quản
        trị viên xác nhận; việc chọn gói chưa tự trừ tiền.
      </p>
    </div>
  );
}
