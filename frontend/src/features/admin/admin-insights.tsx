"use client";

import { useState } from "react";
import { api } from "@/services/api";
import {
  ConfirmDialog,
  DataTable,
  EmptyState,
  ErrorState,
  MetricCard,
  Notice,
  PageHeader,
  Section,
  StatusBadge,
  cellClass,
  fmtDate,
  fmtMoney,
  fmtNumber,
  fmtUsd,
  inputClass,
  secondaryClass,
  useAdminData,
} from "./admin-ui";

type Report = {
  revenue_by_plan: {
    plan_code: string;
    purchases: number;
    revenue_vnd: number;
  }[];
  revenue_today_vnd: number;
  revenue_7d_vnd: number;
  revenue_30d_vnd: number;
  revenue_month_vnd: number;
  total_revenue_vnd: number;
  average_revenue_per_payer_vnd: number | null;
  paid_transactions: number;
  paid_users: number;
  renewal_count: number;
  expired_vip_users: number;
  trial_by_feature: Record<string, number>;
  completed_practices: Record<string, number>;
  full_exams: Record<string, number>;
  most_practiced_skill: string | null;
  average_practices_per_user: number | null;
  registrations: Record<string, number>;
  funnel: Record<string, number | null>;
  total_users: number;
};
const funnelLabels: [string, string][] = [
  ["registered", "Đăng ký"],
  ["started_trial", "Bắt đầu trial"],
  ["completed_trial", "Hoàn thành trial"],
  ["viewed_pricing", "Xem bảng giá"],
  ["started_checkout", "Tạo thanh toán"],
  ["paid", "Đã mua VIP"],
];
export function ReportsPanel() {
  const [tab, setTab] = useState("overview");
  const { data, error, loading, reload } =
    useAdminData<Report>("/admin/reports");
  return (
    <div>
      <PageHeader
        title="Báo cáo"
        description="Người dùng thật, không gồm admin và tài khoản thử. Doanh thu chỉ tính giao dịch PAID."
      />
      <ErrorState message={error} retry={reload} />
      <div className="mb-5 flex gap-1 overflow-x-auto border-b border-slate-200">
        {[
          ["overview", "Tổng quan"],
          ["users", "Người dùng"],
          ["revenue", "Doanh thu"],
          ["usage", "Luyện tập"],
          ["conversion", "Chuyển đổi"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={
              "whitespace-nowrap border-b-2 px-4 py-2.5 text-sm " +
              (tab === key
                ? "border-teal-700 font-semibold text-teal-800"
                : "border-transparent text-slate-500")
            }
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>
      {loading && !data ? (
        <div className="h-72 animate-pulse rounded-lg bg-slate-100" />
      ) : (
        data && (
          <>
            {tab === "overview" && (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <MetricCard
                    label="Người dùng"
                    value={fmtNumber(data.total_users)}
                  />
                  <MetricCard
                    label="Người đã mua"
                    value={fmtNumber(data.paid_users)}
                  />
                  <MetricCard
                    label="Doanh thu · 30 ngày"
                    value={fmtMoney(data.revenue_30d_vnd)}
                  />
                  <MetricCard
                    label="Bài hoàn thành"
                    value={fmtNumber(
                      Object.values(data.completed_practices).reduce(
                        (a, b) => a + b,
                        0,
                      ),
                    )}
                  />
                </div>
                <Section title="Chỉ số vận hành">
                  <div className="grid gap-4 p-5 text-sm sm:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <p className="text-slate-500">Đăng ký · 7 ngày</p>
                      <strong>{fmtNumber(data.registrations["7d"])}</strong>
                    </div>
                    <div>
                      <p className="text-slate-500">Giao dịch đã trả</p>
                      <strong>{fmtNumber(data.paid_transactions)}</strong>
                    </div>
                    <div>
                      <p className="text-slate-500">VIP gia hạn</p>
                      <strong>{fmtNumber(data.renewal_count)}</strong>
                    </div>
                    <div>
                      <p className="text-slate-500">VIP hết hạn</p>
                      <strong>{fmtNumber(data.expired_vip_users)}</strong>
                    </div>
                  </div>
                </Section>
              </div>
            )}
            {tab === "users" && (
              <div className="grid gap-4 md:grid-cols-2">
                <Section title="Đăng ký">
                  <div className="divide-y divide-slate-100 px-5">
                    {[
                      ["today", "Hôm nay"],
                      ["7d", "7 ngày"],
                      ["30d", "30 ngày"],
                    ].map(([key, label]) => (
                      <div
                        key={key}
                        className="flex justify-between py-3 text-sm"
                      >
                        <span>{label}</span>
                        <strong>{fmtNumber(data.registrations[key])}</strong>
                      </div>
                    ))}
                  </div>
                </Section>
                <Section title="Tài khoản & gói">
                  <div className="divide-y divide-slate-100 px-5">
                    {(
                      [
                        ["Tổng người dùng", data.total_users],
                        ["Người đã mua", data.paid_users],
                        ["Giao dịch gia hạn", data.renewal_count],
                        ["VIP đã hết hạn", data.expired_vip_users],
                      ] as [string, number][]
                    ).map(([label, value]) => (
                      <div
                        key={label}
                        className="flex justify-between py-3 text-sm"
                      >
                        <span>{label}</span>
                        <strong>{fmtNumber(value)}</strong>
                      </div>
                    ))}
                  </div>
                </Section>
              </div>
            )}
            {tab === "revenue" && (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <MetricCard
                    label="Hôm nay"
                    value={fmtMoney(data.revenue_today_vnd)}
                  />
                  <MetricCard
                    label="7 ngày"
                    value={fmtMoney(data.revenue_7d_vnd)}
                  />
                  <MetricCard
                    label="30 ngày"
                    value={fmtMoney(data.revenue_30d_vnd)}
                  />
                  <MetricCard
                    label="Toàn thời gian"
                    value={fmtMoney(data.total_revenue_vnd)}
                  />
                </div>
                <Section title="Theo gói">
                  <DataTable
                    headers={["Gói", "Lượt mua", "Doanh thu"]}
                    empty={
                      !data.revenue_by_plan.length && (
                        <EmptyState
                          title="Chưa có doanh thu"
                          description="Doanh thu theo gói sẽ xuất hiện khi có giao dịch PAID."
                        />
                      )
                    }
                  >
                    {data.revenue_by_plan.map((item) => (
                      <tr key={item.plan_code}>
                        <td className={cellClass}>{item.plan_code}</td>
                        <td className={cellClass}>
                          {fmtNumber(item.purchases)}
                        </td>
                        <td className={cellClass}>
                          {fmtMoney(item.revenue_vnd)}
                        </td>
                      </tr>
                    ))}
                  </DataTable>
                  <p className="p-4 text-xs text-slate-500">
                    Trung bình trên người đã mua:{" "}
                    {data.average_revenue_per_payer_vnd == null
                      ? "—"
                      : fmtMoney(data.average_revenue_per_payer_vnd)}
                  </p>
                </Section>
              </div>
            )}
            {tab === "usage" && (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  {Object.entries(data.completed_practices).map(
                    ([skill, count]) => (
                      <MetricCard
                        key={skill}
                        label={skill + " hoàn thành"}
                        value={fmtNumber(count)}
                        hint={
                          fmtNumber(data.full_exams[skill]) + " bài thi đầy đủ"
                        }
                      />
                    ),
                  )}
                  <MetricCard
                    label="Bài / người dùng"
                    value={data.average_practices_per_user ?? "—"}
                  />
                </div>
                <Section title="Trial theo kỹ năng">
                  <div className="divide-y divide-slate-100 px-5">
                    {Object.entries(data.trial_by_feature).map(
                      ([feature, count]) => (
                        <div
                          key={feature}
                          className="flex justify-between py-3 text-sm"
                        >
                          <span>{feature}</span>
                          <strong>{fmtNumber(count)} người</strong>
                        </div>
                      ),
                    )}
                    {!Object.keys(data.trial_by_feature).length && (
                      <EmptyState
                        title="Chưa có lượt trial"
                        description="Lượt dùng trial sẽ xuất hiện sau khi người dùng bắt đầu luyện."
                      />
                    )}
                  </div>
                </Section>
              </div>
            )}
            {tab === "conversion" && (
              <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
                <Section title="Phễu chuyển đổi">
                  <div className="space-y-5 p-5">
                    {funnelLabels.map(([key, label], index) => {
                      const count = data.funnel[key] ?? 0;
                      const pct = data.total_users
                        ? Math.round((count / data.total_users) * 100)
                        : 0;
                      return (
                        <div key={key}>
                          <div className="flex items-baseline justify-between gap-3 text-sm">
                            <span className="font-medium">
                              {index + 1}. {label}
                            </span>
                            <strong>
                              {fmtNumber(count)}{" "}
                              <span className="ml-1 text-xs font-normal text-slate-500">
                                {pct}% người đăng ký
                              </span>
                            </strong>
                          </div>
                          <div className="mt-2 h-2 overflow-hidden rounded bg-slate-100">
                            <div
                              className="h-full rounded bg-teal-700"
                              style={{ width: Math.min(100, pct) + "%" }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Section>
                <Section title="Từ trial đến trả phí">
                  <div className="p-5">
                    <p className="text-3xl font-semibold text-slate-950">
                      {data.funnel.trial_to_paid_percent == null
                        ? "—"
                        : data.funnel.trial_to_paid_percent + "%"}
                    </p>
                    <p className="mt-2 text-sm text-slate-500">
                      Tỷ lệ người đã dùng trial và mua VIP. Các bước trong phễu
                      là số người riêng biệt, có thể không đi theo một thứ tự cố
                      định.
                    </p>
                  </div>
                </Section>
              </div>
            )}
          </>
        )
      )}
    </div>
  );
}

type AIUsage = {
  summary: {
    cost_today_usd: number;
    cost_period_usd: number;
    cost_per_active_user_usd: number | null;
    cost_per_paid_user_usd: number | null;
    active_users: number;
    paid_users: number;
  };
  by_operation: {
    name: string;
    calls: number;
    cost_usd: number | null;
    unknown_cost_calls: number;
  }[];
  by_model: { name: string; calls: number; cost_usd: number | null }[];
  users: {
    id: string;
    email: string;
    cost_usd: number | null;
    calls: number;
    attempts: number;
    tier: string;
    last_active: string | null;
  }[];
  overview: {
    groups?: {
      operation: string;
      input_tokens: number;
      output_tokens: number;
      reasoning_tokens: number;
      cached_input_tokens: number;
    }[];
  };
};
export function AIUsagePanel() {
  const [days, setDays] = useState(30);
  const { data, error, loading, reload } = useAdminData<AIUsage>(
    "/admin/ai-usage?days=" + days,
  );
  return (
    <div>
      <PageHeader
        title="Chi phí AI"
        description="Ước tính chi phí sản phẩm theo tác vụ, model và người dùng."
        action={
          <select
            className={inputClass}
            value={days}
            onChange={(event) => setDays(Number(event.target.value))}
            aria-label="Khoảng thời gian"
          >
            {[1, 7, 30, 90].map((value) => (
              <option key={value} value={value}>
                {value} ngày
              </option>
            ))}
          </select>
        }
      />
      <ErrorState message={error} retry={reload} />
      <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Chi phí hôm nay"
          value={fmtUsd(data?.summary.cost_today_usd)}
        />
        <MetricCard
          label={"Chi phí · " + days + " ngày"}
          value={fmtUsd(data?.summary.cost_period_usd)}
        />
        <MetricCard
          label="Chi phí / người dùng AI"
          value={fmtUsd(data?.summary.cost_per_active_user_usd)}
          hint={(data?.summary.active_users ?? 0) + " người dùng"}
        />
        <MetricCard
          label="Chi phí / VIP đã mua"
          value={fmtUsd(data?.summary.cost_per_paid_user_usd)}
          hint={(data?.summary.paid_users ?? 0) + " người đã mua, đang VIP"}
        />
      </div>
      {loading && !data ? (
        <div className="h-80 animate-pulse rounded-lg bg-slate-100" />
      ) : (
        data && (
          <div className="space-y-4">
            <div className="grid gap-4 xl:grid-cols-2">
              <Section title="Theo tác vụ">
                <DataTable
                  headers={["Tác vụ", "Lượt gọi", "Chi phí", "Chưa rõ giá"]}
                  empty={
                    !data.by_operation.length && (
                      <EmptyState
                        title="Chưa có lượt AI"
                        description="Chi phí sẽ hiện khi sản phẩm gọi AI."
                      />
                    )
                  }
                >
                  {data.by_operation.map((item) => (
                    <tr key={item.name}>
                      <td className={cellClass}>
                        <span className="font-medium">
                          {item.name.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td className={cellClass}>{fmtNumber(item.calls)}</td>
                      <td className={cellClass}>{fmtUsd(item.cost_usd)}</td>
                      <td className={cellClass}>{item.unknown_cost_calls}</td>
                    </tr>
                  ))}
                </DataTable>
              </Section>
              <Section title="Theo model">
                <DataTable
                  headers={["Model", "Lượt gọi", "Chi phí"]}
                  empty={
                    !data.by_model.length && (
                      <EmptyState
                        title="Chưa có dữ liệu model"
                        description="Model đã dùng sẽ hiện tại đây."
                      />
                    )
                  }
                >
                  {data.by_model.map((item) => (
                    <tr key={item.name}>
                      <td className={cellClass}>{item.name}</td>
                      <td className={cellClass}>{fmtNumber(item.calls)}</td>
                      <td className={cellClass}>{fmtUsd(item.cost_usd)}</td>
                    </tr>
                  ))}
                </DataTable>
              </Section>
            </div>
            <Section title="Người dùng có chi phí cao">
              <DataTable
                headers={[
                  "Người dùng",
                  "Bài luyện",
                  "Lượt gọi",
                  "Chi phí",
                  "Quyền",
                  "Hoạt động",
                ]}
                minWidth={740}
                empty={
                  !data.users.length && (
                    <EmptyState
                      title="Chưa có chi phí người dùng"
                      description="Danh sách này chỉ hiện lượt AI của sản phẩm."
                    />
                  )
                }
              >
                {data.users.map((user) => (
                  <tr key={user.id}>
                    <td className={cellClass}>
                      <a
                        href={"/admin/user?id=" + user.id}
                        className="font-medium text-teal-800"
                      >
                        {user.email}
                      </a>
                    </td>
                    <td className={cellClass}>{fmtNumber(user.attempts)}</td>
                    <td className={cellClass}>{fmtNumber(user.calls)}</td>
                    <td className={cellClass}>{fmtUsd(user.cost_usd)}</td>
                    <td className={cellClass}>
                      <StatusBadge status={user.tier} />
                    </td>
                    <td className={cellClass}>{fmtDate(user.last_active)}</td>
                  </tr>
                ))}
              </DataTable>
            </Section>
            <details className="rounded-lg border border-slate-200 bg-white">
              <summary className="cursor-pointer px-5 py-3 text-sm font-medium">
                Thông số token nâng cao
              </summary>
              <DataTable
                headers={["Tác vụ", "Input", "Cache", "Output", "Reasoning"]}
              >
                {data.overview.groups?.map((group, index) => (
                  <tr key={index}>
                    <td className={cellClass}>{group.operation}</td>
                    <td className={cellClass}>
                      {fmtNumber(group.input_tokens)}
                    </td>
                    <td className={cellClass}>
                      {fmtNumber(group.cached_input_tokens)}
                    </td>
                    <td className={cellClass}>
                      {fmtNumber(group.output_tokens)}
                    </td>
                    <td className={cellClass}>
                      {fmtNumber(group.reasoning_tokens)}
                    </td>
                  </tr>
                ))}
              </DataTable>
            </details>
          </div>
        )
      )}
    </div>
  );
}

type Plan = {
  id: string;
  code: string;
  name: string;
  duration_days: number;
  price_vnd: number;
  is_active: boolean;
  active_users: number;
};
const flagGroups: [string, [string, string][]][] = [
  [
    "Tính năng",
    [
      ["user_custom_questions_enabled", "Đề riêng của người học"],
      ["vip_ai_question_generation_enabled", "VIP sinh đề AI"],
      ["free_ai_question_generation_enabled", "Free sinh đề AI"],
      ["free_reading_enabled", "Reading miễn phí"],
    ],
  ],
  [
    "Trial",
    [
      ["free_trial_writing_task1_attempts", "Writing Task 1"],
      ["free_trial_speaking_part1_attempts", "Speaking Part 1"],
      ["free_reading_daily_limit", "Reading miễn phí / ngày"],
    ],
  ],
  [
    "Hạn mức",
    [
      ["vip_fair_use_enabled", "Bật giới hạn hợp lý"],
      ["vip_writing_daily_limit", "Writing / ngày"],
      ["vip_speaking_daily_limit", "Speaking / ngày"],
      ["vip_reading_daily_limit", "Reading / ngày"],
      ["vip_ai_generation_daily_limit", "Sinh đề AI / ngày"],
    ],
  ],
];
export function SettingsPanel() {
  const config = useAdminData<Record<string, unknown>>("/admin/settings");
  const plans = useAdminData<{ items: Plan[] }>("/admin/plans");
  const audit = useAdminData<{
    items: {
      id: string;
      action: string;
      target_type: string;
      created_at: string;
    }[];
  }>("/admin/audit-logs?limit=15");
  const [edits, setEdits] = useState<Record<string, Partial<Plan>>>({}),
    [saving, setSaving] = useState<Plan | null>(null),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState("");
  async function save() {
    if (!saving) return;
    setBusy(true);
    try {
      await api("/admin/plans/" + saving.code, {
        method: "PATCH",
        body: JSON.stringify(edits[saving.code]),
      });
      setSaving(null);
      setNotice("Đã cập nhật gói VIP.");
      plans.reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div>
      <PageHeader
        title="Cấu hình"
        description="Quản lý gói VIP và xem chính sách đang áp dụng."
      />
      <Notice text={notice} onClose={() => setNotice("")} />
      <ErrorState
        message={error || plans.error || config.error}
        retry={() => {
          plans.reload();
          config.reload();
        }}
      />
      <Section title="Gói VIP">
        <div className="divide-y divide-slate-100">
          {plans.data?.items.map((plan) => {
            const edit = { ...plan, ...edits[plan.code] };
            return (
              <div
                key={plan.code}
                className="grid items-end gap-3 px-5 py-4 sm:grid-cols-[1fr_120px_130px_110px_auto]"
              >
                <label className="text-xs font-medium text-slate-500">
                  Tên gói
                  <input
                    className={inputClass + " mt-1 w-full"}
                    value={edit.name}
                    onChange={(event) =>
                      setEdits({
                        ...edits,
                        [plan.code]: {
                          ...edits[plan.code],
                          name: event.target.value,
                        },
                      })
                    }
                  />
                </label>
                <label className="text-xs font-medium text-slate-500">
                  Thời hạn (ngày)
                  <input
                    type="number"
                    min={1}
                    max={365}
                    className={inputClass + " mt-1 w-full"}
                    value={edit.duration_days}
                    onChange={(event) =>
                      setEdits({
                        ...edits,
                        [plan.code]: {
                          ...edits[plan.code],
                          duration_days: Number(event.target.value),
                        },
                      })
                    }
                  />
                </label>
                <label className="text-xs font-medium text-slate-500">
                  Giá (VND)
                  <input
                    type="number"
                    min={0}
                    className={inputClass + " mt-1 w-full"}
                    value={edit.price_vnd}
                    onChange={(event) =>
                      setEdits({
                        ...edits,
                        [plan.code]: {
                          ...edits[plan.code],
                          price_vnd: Number(event.target.value),
                        },
                      })
                    }
                  />
                </label>
                <div className="text-xs text-slate-500">
                  <p>{plan.active_users} VIP đang dùng</p>
                  <label className="mt-2 flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={edit.is_active}
                      onChange={(event) =>
                        setEdits({
                          ...edits,
                          [plan.code]: {
                            ...edits[plan.code],
                            is_active: event.target.checked,
                          },
                        })
                      }
                    />
                    Đang bán
                  </label>
                </div>
                <button
                  className={secondaryClass}
                  disabled={!edits[plan.code]}
                  onClick={() => setSaving(plan)}
                >
                  Lưu
                </button>
              </div>
            );
          })}
          {!plans.data?.items.length && (
            <EmptyState
              title="Chưa có gói VIP"
              description="Các gói được khởi tạo qua migration."
            />
          )}
        </div>
      </Section>
      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        {flagGroups.map(([group, fields]) => (
          <Section key={group} title={group}>
            <div className="divide-y divide-slate-100 px-5">
              {fields.map(([key, label]) => (
                <div
                  key={key}
                  className="flex items-center justify-between gap-3 py-3 text-sm"
                >
                  <div>
                    <p>{label}</p>
                    <p className="text-[11px] text-slate-400">{key}</p>
                  </div>
                  {typeof config.data?.[key] === "boolean" ? (
                    <StatusBadge status={config.data[key] ? "ON" : "OFF"} />
                  ) : (
                    <strong>{String(config.data?.[key] ?? "—")}</strong>
                  )}
                </div>
              ))}
            </div>
          </Section>
        ))}
      </div>
      <Section title="AI và thanh toán" className="mt-5">
        <div className="grid gap-4 p-5 text-sm sm:grid-cols-2">
          <div>
            <p className="text-slate-500">Phương thức thanh toán</p>
            <strong>{String(config.data?.payment_provider || "—")}</strong>
          </div>
          <div>
            <p className="text-slate-500">Cấu hình AI</p>
            <strong>Được quản lý ở backend</strong>
            <p className="mt-1 text-xs text-slate-500">
              Khóa API không hiển thị trên trang quản trị.
            </p>
          </div>
        </div>
        <p className="border-t px-5 py-3 text-xs text-slate-500">
          Các cờ tính năng và hạn mức là chỉ đọc. Thay đổi qua môi trường triển
          khai để giữ quy trình kiểm soát.
        </p>
      </Section>
      <details className="mt-5 rounded-lg border border-slate-200 bg-white">
        <summary className="cursor-pointer px-5 py-4 text-sm font-medium">
          Nhật ký thao tác gần đây
        </summary>
        <div className="divide-y divide-slate-100 px-5">
          {audit.data?.items.map((item) => (
            <div
              key={item.id}
              className="flex justify-between gap-3 py-2 text-xs"
            >
              <span>
                {item.action} · {item.target_type}
              </span>
              <span className="text-slate-500">{fmtDate(item.created_at)}</span>
            </div>
          ))}
        </div>
      </details>
      <ConfirmDialog
        open={!!saving}
        onOpenChange={(open) => {
          if (!open) setSaving(null);
        }}
        title="Lưu thay đổi gói VIP?"
        description={
          "Giá và thời hạn mới sẽ áp dụng cho giao dịch được tạo sau khi lưu. Thanh toán đã tạo giữ giá chụp tại thời điểm chọn gói."
        }
        confirmLabel="Lưu gói"
        onConfirm={save}
        busy={busy}
      >
        <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm">
          {saving?.name} →{" "}
          {saving
            ? fmtMoney(edits[saving.code]?.price_vnd ?? saving.price_vnd)
            : ""}
        </div>
      </ConfirmDialog>
    </div>
  );
}
