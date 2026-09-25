"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/features/auth/auth-provider";
import { api } from "@/services/api";
import { ErrorNotice } from "@/components/feedback";

type Entitlement = {
  id: string;
  source: string;
  status: string;
  starts_at: string;
  expires_at: string;
  reason?: string | null;
};
type Payment = {
  id: string;
  status: string;
  amount_vnd: number;
  created_at: string;
  paid_at: string | null;
  plan_snapshot: { plan_name?: string };
};
const date = (value?: string | null) =>
  value
    ? new Intl.DateTimeFormat("vi-VN", {
        dateStyle: "short",
        timeStyle: "short",
        timeZone: "Asia/Ho_Chi_Minh",
      }).format(new Date(value))
    : "—";
function Content() {
  const [data, setData] = useState<{
    access: {
      tier: string;
      vip_expires_at: string | null;
      trial_remaining: Record<string, number>;
    };
    current: Entitlement | null;
    current_plan: { name: string } | null;
    history: Entitlement[];
    server_now: string;
  } | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    api<typeof data>("/subscription/me")
      .then(setData)
      .catch((e) => setError(e.message));
    api<{ items: Payment[] }>("/payments/me")
      .then((p) => setPayments(p.items))
      .catch((e) => setError(e.message));
  }, []);
  return (
    <div className="space-y-7">
      <div>
        <p className="eyebrow">Quyền truy cập</p>
        <h1 className="mt-2 text-3xl font-bold">Gói và thanh toán</h1>
      </div>
      {error && <ErrorNotice message={error} />}
      <div className="panel p-6">
        <p className="text-sm text-stone-500">Gói hiện tại</p>
        <p className="mt-1 text-2xl font-bold">
          {data?.access.tier === "VIP"
            ? data.current_plan?.name || "VIP được cấp"
            : data?.access.tier || "Đang tải…"}
        </p>
        {data?.current && (
          <p className="mt-2 text-sm text-stone-600">
            Đang hoạt động · Bắt đầu: {date(data.current.starts_at)} · Hết hạn:{" "}
            {date(data.access.vip_expires_at)} · Còn{" "}
            {Math.max(
              0,
              Math.ceil(
                (new Date(data.access.vip_expires_at || 0).getTime() -
                  new Date(data.server_now).getTime()) /
                  86400000,
              ),
            )}{" "}
            ngày
          </p>
        )}
        {data?.access.tier === "FREE" && (
          <p className="mt-2 text-sm text-stone-600">
            Trial còn lại: Writing Task 1{" "}
            {data.access.trial_remaining.WRITING_TASK1 ?? 0}, Speaking Part 1{" "}
            {data.access.trial_remaining.SPEAKING_PART1 ?? 0}.
          </p>
        )}
        <Link
          href="/pricing"
          className="mt-5 inline-block rounded-xl bg-teal-800 px-5 py-3 text-sm font-semibold text-white"
        >
          {data?.access.tier === "VIP" ? "Gia hạn VIP" : "Nâng cấp VIP"}
        </Link>
      </div>
      <section>
        <h2 className="mb-3 text-xl font-bold">Thanh toán</h2>
        <div className="panel divide-y divide-stone-100">
          {payments.length ? (
            payments.map((p) => (
              <div
                key={p.id}
                className="flex flex-wrap justify-between gap-3 p-4 text-sm"
              >
                <span>
                  {p.plan_snapshot.plan_name || "Gói VIP"} ·{" "}
                  {new Intl.NumberFormat("vi-VN").format(p.amount_vnd)}đ
                </span>
                <span className="font-semibold">
                  {p.status === "PENDING"
                    ? "Chờ xác nhận thủ công"
                    : p.status === "PAID"
                      ? "Đã thanh toán"
                      : p.status}
                </span>
                <span className="text-stone-500">
                  {date(p.paid_at || p.created_at)}
                </span>
              </div>
            ))
          ) : (
            <p className="p-4 text-sm text-stone-500">Chưa có thanh toán.</p>
          )}
        </div>
        {payments.some((p) => p.status === "PENDING") && (
          <p className="mt-3 text-sm text-stone-600">
            Yêu cầu đang chờ xác nhận. Liên hệ hỗ trợ để nhận hướng dẫn chuyển
            khoản; VIP chưa được kích hoạt.
          </p>
        )}
      </section>
      <section>
        <h2 className="mb-3 text-xl font-bold">Lịch sử VIP</h2>
        <div className="panel divide-y divide-stone-100">
          {data?.history.length ? (
            data.history.map((e) => (
              <div key={e.id} className="p-4 text-sm">
                {e.source === "PURCHASE" ? "Thanh toán" : "Quản trị cấp"} ·{" "}
                {date(e.starts_at)} → {date(e.expires_at)} · {e.status}
              </div>
            ))
          ) : (
            <p className="p-4 text-sm text-stone-500">Chưa có gói VIP.</p>
          )}
        </div>
      </section>
    </div>
  );
}
export default function SubscriptionPage() {
  return (
    <RequireAuth>
      <Content />
    </RequireAuth>
  );
}
