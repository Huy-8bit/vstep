"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowRight, Clock3, CreditCard, FileQuestion } from "lucide-react";
import {
  DataTable,
  EmptyState,
  ErrorState,
  MetricCard,
  PageHeader,
  Section,
  StatusBadge,
  cellClass,
  fmtDate,
  fmtMoney,
  fmtNumber,
  fmtRemaining,
  fmtUsd,
  secondaryClass,
  useAdminData,
} from "./admin-ui";

type Summary = {
  total_users: number;
  active_users_month: number;
  vip_users: number;
  paid_vip_users: number;
  new_users_today: number;
  total_vip_purchases: number;
  revenue_30d_vnd: number;
  ai_cost_today_usd: number;
  ai_cost_30d_usd: number;
  vip_conversion_rate: number | null;
  vip_expiring: Record<string, number>;
};
type Point = { day: string; users: number; revenue_vnd: number };
type Operations = {
  recent_payments: {
    id: string;
    email: string;
    status: string;
    amount_vnd: number;
    created_at: string;
    user_id: string;
  }[];
  recent_users: {
    id: string;
    name: string | null;
    email: string;
    created_at: string;
  }[];
  expiring_vip: {
    id: string;
    user_id: string;
    email: string;
    expires_at: string;
    plan_id: string | null;
  }[];
  high_cost_users: { id: string; email: string; cost_usd: number | null }[];
  attention: { pending_payments_over_1h: number; question_drafts: number };
  server_now: string;
};
const chartTooltip = { borderRadius: 8, borderColor: "#e2e8f0", fontSize: 12 };

export function DashboardPanel() {
  const [days, setDays] = useState(30);
  const summary = useAdminData<Summary>("/admin/dashboard");
  const series = useAdminData<{ items: Point[] }>(
    "/admin/dashboard/series?days=" + days,
  );
  const operations = useAdminData<Operations>("/admin/dashboard/operations");
  const metrics = [
    {
      label: "Tổng người dùng",
      value: fmtNumber(summary.data?.total_users),
      hint: "Tài khoản thật, không gồm test/admin",
    },
    {
      label: "VIP đang hoạt động",
      value: fmtNumber(summary.data?.vip_users),
      hint: (summary.data?.paid_vip_users ?? 0) + " người mua gói",
    },
    {
      label: "Doanh thu · 30 ngày",
      value: fmtMoney(summary.data?.revenue_30d_vnd),
      hint: "Chỉ giao dịch đã thanh toán",
    },
    {
      label: "Chi phí AI · 30 ngày",
      value: fmtUsd(summary.data?.ai_cost_30d_usd),
      hint: "Ước tính theo lượt đã ghi nhận",
    },
    {
      label: "Đăng ký hôm nay",
      value: fmtNumber(summary.data?.new_users_today),
      hint: "Theo giờ Việt Nam",
    },
    {
      label: "Lượt mua VIP",
      value: fmtNumber(summary.data?.total_vip_purchases),
      hint: "Toàn thời gian",
    },
    {
      label: "Chi phí AI hôm nay",
      value: fmtUsd(summary.data?.ai_cost_today_usd),
      hint: "Không gồm benchmark và test",
    },
    {
      label: "Trial → trả phí",
      value:
        summary.data?.vip_conversion_rate == null
          ? "—"
          : summary.data.vip_conversion_rate + "%",
      hint: "Người dùng trial đã mua VIP",
    },
  ];
  const points = series.data?.items || [];
  const ops = operations.data;
  return (
    <div className="space-y-6">
      <PageHeader
        title="Tổng quan"
        description="Sức khỏe sản phẩm và các việc cần xử lý hôm nay."
        action={
          <Link href="/admin/reports" className={secondaryClass}>
            Xem báo cáo <ArrowRight size={15} />
          </Link>
        }
      />
      <ErrorState
        message={summary.error || series.error || operations.error}
        retry={() => {
          summary.reload();
          series.reload();
          operations.reload();
        }}
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard
            key={metric.label}
            label={metric.label}
            value={
              summary.loading ? (
                <span className="inline-block h-7 w-20 animate-pulse rounded bg-slate-100" />
              ) : (
                metric.value
              )
            }
            hint={metric.hint}
          />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Section
          title="Người dùng mới"
          action={
            <span className="text-xs text-slate-500">{days} ngày gần đây</span>
          }
        >
          <div className="h-56 p-4">
            {series.loading ? (
              <div className="h-full animate-pulse rounded bg-slate-50" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={points}>
                  <CartesianGrid stroke="#e9eef1" vertical={false} />
                  <XAxis
                    dataKey="day"
                    tickFormatter={(value: string) => value.slice(5)}
                    tick={{ fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip contentStyle={chartTooltip} />
                  <Area
                    type="monotone"
                    dataKey="users"
                    name="Đăng ký"
                    stroke="#0f766e"
                    fill="#d6f0ec"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </Section>
        <Section
          title="Doanh thu đã thanh toán"
          action={
            <div className="flex rounded-md border border-slate-200 p-0.5">
              {[7, 30].map((value) => (
                <button
                  key={value}
                  aria-pressed={days === value}
                  className={
                    "rounded px-2.5 py-1 text-xs " +
                    (days === value
                      ? "bg-slate-100 font-semibold text-slate-900"
                      : "text-slate-500")
                  }
                  onClick={() => setDays(value)}
                >
                  {value} ngày
                </button>
              ))}
            </div>
          }
        >
          <div className="h-56 p-4">
            {series.loading ? (
              <div className="h-full animate-pulse rounded bg-slate-50" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={points}>
                  <CartesianGrid stroke="#e9eef1" vertical={false} />
                  <XAxis
                    dataKey="day"
                    tickFormatter={(value: string) => value.slice(5)}
                    tick={{ fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tickFormatter={(value: number) =>
                      value >= 1000000
                        ? fmtNumber(value / 1000000) + "tr"
                        : value >= 1000
                          ? fmtNumber(value / 1000) + "k"
                          : String(value)
                    }
                    tick={{ fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={chartTooltip}
                    formatter={(value) => fmtMoney(Number(value))}
                  />
                  <Bar
                    dataKey="revenue_vnd"
                    name="Doanh thu"
                    fill="#0f766e"
                    radius={[3, 3, 0, 0]}
                    maxBarSize={24}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Section>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1fr_1.4fr]">
        <Section
          title="Cần xử lý"
          action={
            <Link
              className="text-xs font-semibold text-teal-800"
              href="/admin/payments"
            >
              Mở thanh toán →
            </Link>
          }
        >
          <div className="divide-y divide-slate-100 px-5">
            <Link
              href="/admin/payments?status=PENDING"
              className="flex items-center justify-between gap-3 py-4 text-sm"
            >
              <span className="flex items-center gap-2 text-slate-700">
                <CreditCard size={16} className="text-amber-600" />
                Khoản chờ quá 1 giờ
              </span>
              <strong>{ops?.attention.pending_payments_over_1h ?? "—"}</strong>
            </Link>
            <Link
              href="/admin/subscriptions?state=expiring"
              className="flex items-center justify-between gap-3 py-4 text-sm"
            >
              <span className="flex items-center gap-2 text-slate-700">
                <Clock3 size={16} className="text-amber-600" />
                VIP hết hạn trong 24 giờ
              </span>
              <strong>{summary.data?.vip_expiring["24h"] ?? "—"}</strong>
            </Link>
            <Link
              href="/admin/questions?publication=draft"
              className="flex items-center justify-between gap-3 py-4 text-sm"
            >
              <span className="flex items-center gap-2 text-slate-700">
                <FileQuestion size={16} className="text-slate-500" />
                Đề nháp cần duyệt
              </span>
              <strong>{ops?.attention.question_drafts ?? "—"}</strong>
            </Link>
          </div>
        </Section>
        <Section
          title="VIP sắp hết hạn"
          action={
            <Link
              className="text-xs font-semibold text-teal-800"
              href="/admin/subscriptions?state=expiring"
            >
              Xem tất cả →
            </Link>
          }
        >
          <div className="divide-y divide-slate-100">
            {ops?.expiring_vip.length ? (
              ops.expiring_vip.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-3 px-5 py-3 text-sm"
                >
                  <Link
                    href={"/admin/user?id=" + item.user_id}
                    className="min-w-0 truncate font-medium text-slate-800 hover:text-teal-800"
                  >
                    {item.email}
                  </Link>
                  <span className="shrink-0 text-xs text-slate-500">
                    {fmtDate(item.expires_at)}
                  </span>
                  <span className="shrink-0 text-xs font-semibold text-amber-700">
                    {fmtRemaining(
                      (new Date(item.expires_at).getTime() -
                        new Date(ops.server_now).getTime()) /
                        1000,
                    )}
                  </span>
                </div>
              ))
            ) : (
              <EmptyState
                title="Chưa có VIP sắp hết hạn"
                description="Các gói hết hạn trong 7 ngày tới sẽ xuất hiện ở đây."
              />
            )}
          </div>
        </Section>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Section
          title="Thanh toán gần đây"
          action={
            <Link
              className="text-xs font-semibold text-teal-800"
              href="/admin/payments"
            >
              Xem tất cả →
            </Link>
          }
        >
          <DataTable
            headers={["Người dùng", "Số tiền", "Trạng thái"]}
            minWidth={430}
            loading={operations.loading}
            empty={
              !ops?.recent_payments.length && (
                <EmptyState
                  title="Chưa có thanh toán"
                  description="Khoản thanh toán sẽ xuất hiện sau khi người dùng chọn gói."
                />
              )
            }
          >
            {ops?.recent_payments.map((item) => (
              <tr key={item.id}>
                <td className={cellClass}>
                  <Link
                    href={"/admin/user?id=" + item.user_id}
                    className="block max-w-48 truncate font-medium text-teal-800"
                  >
                    {item.email}
                  </Link>
                </td>
                <td className={cellClass}>{fmtMoney(item.amount_vnd)}</td>
                <td className={cellClass}>
                  <StatusBadge status={item.status} />
                </td>
              </tr>
            ))}
          </DataTable>
        </Section>
        <Section
          title="Người dùng mới"
          action={
            <Link
              className="text-xs font-semibold text-teal-800"
              href="/admin/users"
            >
              Xem tất cả →
            </Link>
          }
        >
          <DataTable
            headers={["Người dùng", "Đăng ký"]}
            minWidth={380}
            loading={operations.loading}
            empty={
              !ops?.recent_users.length && (
                <EmptyState
                  title="Chưa có người dùng"
                  description="Tài khoản mới sẽ xuất hiện ở đây."
                />
              )
            }
          >
            {ops?.recent_users.map((item) => (
              <tr key={item.id}>
                <td className={cellClass}>
                  <Link
                    href={"/admin/user?id=" + item.id}
                    className="font-medium text-teal-800"
                  >
                    {item.name || item.email}
                  </Link>
                  <p className="text-xs text-slate-500">{item.email}</p>
                </td>
                <td className={cellClass}>{fmtDate(item.created_at)}</td>
              </tr>
            ))}
          </DataTable>
        </Section>
      </div>
      {ops?.high_cost_users.length ? (
        <Section
          title="Người dùng có chi phí AI cao · 30 ngày"
          action={
            <Link
              className="text-xs font-semibold text-teal-800"
              href="/admin/ai-usage"
            >
              Chi tiết →
            </Link>
          }
        >
          <div className="flex flex-wrap gap-x-8 gap-y-2 px-5 py-4">
            {ops.high_cost_users.map((item) => (
              <Link
                key={item.id}
                href={"/admin/user?id=" + item.id}
                className="text-xs text-slate-600 hover:text-teal-800"
              >
                {item.email}{" "}
                <strong className="ml-1 text-slate-900">
                  {fmtUsd(item.cost_usd)}
                </strong>
              </Link>
            ))}
          </div>
        </Section>
      ) : null}
    </div>
  );
}
