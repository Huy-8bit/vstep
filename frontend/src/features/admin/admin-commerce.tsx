"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { post } from "@/services/api";
import {
  ActionMenu,
  ConfirmDialog,
  DataTable,
  DetailDrawer,
  EmptyState,
  ErrorState,
  FilterBar,
  MetricCard,
  Notice,
  PageHeader,
  Pagination,
  SearchInput,
  Section,
  StatusBadge,
  cellClass,
  fmtDate,
  fmtMoney,
  fmtNumber,
  fmtRemaining,
  inputClass,
  primaryClass,
  secondaryClass,
  useAdminData,
  type ListResponse,
} from "./admin-ui";

type Subscription = {
  id: string;
  user_id: string;
  email: string;
  plan_name: string | null;
  source: string;
  starts_at: string;
  expires_at: string;
  remaining_seconds: number;
  status: string;
  payment_id: string | null;
};
type Payment = {
  id: string;
  user_id: string;
  email: string;
  amount_vnd: number;
  currency: string;
  plan_snapshot: {
    plan_code: string;
    plan_name: string;
    duration_days: number;
  };
  provider: string;
  provider_payment_id: string | null;
  status: string;
  created_at: string;
  paid_at: string | null;
};
type PaymentDetail = Payment & {
  entitlement: {
    id: string;
    starts_at: string;
    expires_at: string;
    status: string;
  } | null;
};

export function SubscriptionsPanel() {
  const router = useRouter(),
    params = useSearchParams();
  const state = params.get("state") || "active",
    page = Math.max(1, Number(params.get("page") || 1)),
    pageSize = 25;
  const { data, error, loading, reload } = useAdminData<
    ListResponse<Subscription>
  >(
    "/admin/subscriptions?state=" +
      state +
      "&offset=" +
      (page - 1) * pageSize +
      "&limit=" +
      pageSize,
  );
  const summary = useAdminData<{
    vip_users: number;
    paid_vip_users: number;
    admin_granted_vip_users: number;
    vip_expiring: Record<string, number>;
  }>("/admin/dashboard");
  function setState(value: string) {
    router.replace("/admin/subscriptions?state=" + value);
  }
  return (
    <div>
      <PageHeader
        title="Gói VIP"
        description="Theo dõi quyền đang hiệu lực, sắp hết hạn và lịch sử cấp gói."
      />
      <ErrorState
        message={error || summary.error}
        retry={() => {
          reload();
          summary.reload();
        }}
      />
      <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="VIP đang hoạt động"
          value={fmtNumber(summary.data?.vip_users)}
        />
        <MetricCard
          label="VIP đã mua"
          value={fmtNumber(summary.data?.paid_vip_users)}
        />
        <MetricCard
          label="VIP admin cấp"
          value={fmtNumber(summary.data?.admin_granted_vip_users)}
        />
        <MetricCard
          label="Hết hạn trong 7 ngày"
          value={fmtNumber(summary.data?.vip_expiring["7d"])}
        />
      </div>
      <FilterBar>
        <div className="flex flex-wrap gap-1">
          {[
            ["active", "Đang hoạt động"],
            ["expiring", "Sắp hết hạn"],
            ["expired", "Đã hết hạn"],
            ["manual", "Admin cấp"],
            ["purchased", "Đã mua"],
            ["all", "Tất cả"],
          ].map(([key, label]) => (
            <button
              key={key}
              aria-pressed={state === key}
              className={state === key ? primaryClass : secondaryClass}
              onClick={() => setState(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </FilterBar>
      <DataTable
        headers={[
          "Người dùng",
          "Gói",
          "Nguồn",
          "Bắt đầu",
          "Hết hạn",
          "Còn lại",
          "Trạng thái",
          "",
        ]}
        loading={loading}
        minWidth={940}
        empty={
          !data?.items.length && (
            <EmptyState
              title="Không có gói VIP trong nhóm này"
              description="Thử một bộ lọc khác để xem lịch sử gói."
            />
          )
        }
      >
        {data?.items.map((item) => (
          <tr key={item.id} className="hover:bg-slate-50/70">
            <td className={cellClass}>
              <Link
                href={"/admin/user?id=" + item.user_id + "&tab=subscription"}
                className="font-medium text-teal-800"
              >
                {item.email}
              </Link>
            </td>
            <td className={cellClass}>{item.plan_name || "Cấp thủ công"}</td>
            <td className={cellClass}>
              <StatusBadge status={item.source} />
            </td>
            <td className={cellClass}>{fmtDate(item.starts_at)}</td>
            <td className={cellClass}>{fmtDate(item.expires_at)}</td>
            <td className={cellClass}>
              {fmtRemaining(item.remaining_seconds)}
            </td>
            <td className={cellClass}>
              <StatusBadge status={item.status} />
            </td>
            <td className={cellClass}>
              <ActionMenu
                actions={[
                  {
                    label: "Xem người dùng",
                    onClick: () =>
                      router.push(
                        "/admin/user?id=" + item.user_id + "&tab=subscription",
                      ),
                  },
                  {
                    label: "Gia hạn VIP",
                    onClick: () =>
                      router.push(
                        "/admin/user?id=" +
                          item.user_id +
                          "&tab=subscription&grant=1",
                      ),
                  },
                ]}
              />
            </td>
          </tr>
        ))}
      </DataTable>
      <Pagination
        page={page}
        pageSize={pageSize}
        total={data?.total || 0}
        onPage={(value) =>
          router.replace(
            "/admin/subscriptions?state=" + state + "&page=" + value,
          )
        }
      />
    </div>
  );
}

function PaymentDetailContent({ id }: { id: string }) {
  const { data, error, loading, reload } = useAdminData<PaymentDetail>(
    "/admin/payments/" + id,
  );
  if (loading && !data)
    return <div className="h-64 animate-pulse rounded-lg bg-slate-100" />;
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return null;
  return (
    <div className="space-y-5 text-sm">
      <div className="rounded-lg bg-slate-50 p-4">
        <p className="text-2xl font-semibold">{fmtMoney(data.amount_vnd)}</p>
        <div className="mt-2">
          <StatusBadge status={data.status} />
        </div>
        <p className="mt-3 text-slate-500">
          {data.plan_snapshot.plan_name} · {data.plan_snapshot.duration_days}{" "}
          ngày
        </p>
      </div>
      <dl className="space-y-0 divide-y divide-slate-100">
        {[
          ["Người dùng", data.email],
          ["Nhà cung cấp", data.provider],
          ["Mã giao dịch", data.provider_payment_id || "—"],
          ["Tạo lúc", fmtDate(data.created_at)],
          ["Đã trả lúc", fmtDate(data.paid_at)],
          ["ID thanh toán", data.id],
        ].map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 py-3">
            <dt className="text-slate-500">{label}</dt>
            <dd className="break-all text-right font-medium">{value}</dd>
          </div>
        ))}
      </dl>
      {data.entitlement ? (
        <Section title="Quyền VIP đã tạo">
          <div className="space-y-2 p-4">
            <p>Bắt đầu: {fmtDate(data.entitlement.starts_at)}</p>
            <p>Hết hạn: {fmtDate(data.entitlement.expires_at)}</p>
            <StatusBadge status={data.entitlement.status} />
          </div>
        </Section>
      ) : (
        <p className="rounded-md bg-amber-50 p-3 text-amber-800">
          Chưa có quyền VIP từ thanh toán này.
        </p>
      )}
      <details className="text-xs text-slate-500">
        <summary className="cursor-pointer">Thông tin kỹ thuật</summary>
        <p className="mt-2 break-all">
          Payment ID: {data.id}
          <br />
          Plan code: {data.plan_snapshot.plan_code}
        </p>
      </details>
    </div>
  );
}

export function PaymentsPanel() {
  const router = useRouter(),
    params = useSearchParams();
  const status = params.get("status") || "PENDING",
    page = Math.max(1, Number(params.get("page") || 1)),
    pageSize = 25,
    search = params.get("search") || "";
  const [draft, setDraft] = useState(search),
    [selected, setSelected] = useState<Payment | null>(null),
    [confirming, setConfirming] = useState<Payment | null>(null);
  const [reference, setReference] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const { data, error, setError, loading, reload } = useAdminData<
    ListResponse<Payment>
  >(
    "/admin/payments?" +
      new URLSearchParams({
        status,
        search,
        sort: params.get("sort") || "created_desc",
        offset: String((page - 1) * pageSize),
        limit: String(pageSize),
      }),
  );
  const summary = useAdminData<{
    revenue_today_vnd: number;
    revenue_7d_vnd: number;
    revenue_30d_vnd: number;
    successful_payments: number;
    pending_payments: number;
  }>("/admin/payments/summary");
  function update(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value && value !== "all") next.set(key, value);
    else next.delete(key);
    next.delete("page");
    router.replace("/admin/payments?" + next.toString());
  }
  async function confirmPayment() {
    if (!confirming) return;
    setBusy(true);
    try {
      await post("/admin/payments/" + confirming.id + "/confirm", {
        reference: reference.trim(),
        reason: "Đã đối soát chuyển khoản",
      });
      setNotice("Đã ghi nhận thanh toán và kích hoạt VIP.");
      setConfirming(null);
      setReference("");
      reload();
      summary.reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div>
      <PageHeader
        title="Thanh toán"
        description="Đối soát chuyển khoản, theo dõi giao dịch và doanh thu thực nhận."
      />
      <Notice text={notice} onClose={() => setNotice("")} />
      <ErrorState
        message={error || summary.error}
        retry={() => {
          reload();
          summary.reload();
        }}
      />
      <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Doanh thu hôm nay"
          value={fmtMoney(summary.data?.revenue_today_vnd)}
        />
        <MetricCard
          label="Doanh thu · 7 ngày"
          value={fmtMoney(summary.data?.revenue_7d_vnd)}
        />
        <MetricCard
          label="Doanh thu · 30 ngày"
          value={fmtMoney(summary.data?.revenue_30d_vnd)}
        />
        <MetricCard
          label="Giao dịch đã trả"
          value={fmtNumber(summary.data?.successful_payments)}
          hint={(summary.data?.pending_payments ?? 0) + " khoản đang chờ"}
        />
      </div>
      <FilterBar>
        <form
          className="flex min-w-52 flex-1 gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            update("search", draft.trim());
          }}
        >
          <SearchInput
            value={draft}
            onChange={setDraft}
            placeholder="Email hoặc mã giao dịch"
          />
          <button className={secondaryClass}>Tìm</button>
        </form>
        <select
          className={inputClass}
          aria-label="Trạng thái"
          value={status}
          onChange={(event) => update("status", event.target.value)}
        >
          {[
            ["all", "Mọi trạng thái"],
            ["PENDING", "Chờ đối soát"],
            ["PAID", "Đã trả"],
            ["FAILED", "Thất bại"],
            ["REFUNDED", "Hoàn tiền"],
            ["CANCELLED", "Đã hủy"],
            ["EXPIRED", "Hết hạn"],
          ].map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
        <select
          className={inputClass}
          aria-label="Sắp xếp"
          value={params.get("sort") || "created_desc"}
          onChange={(event) => update("sort", event.target.value)}
        >
          <option value="created_desc">Tạo gần đây</option>
          <option value="amount_desc">Số tiền cao</option>
          <option value="paid_desc">Trả gần đây</option>
        </select>
        <button
          className={secondaryClass}
          onClick={() => {
            setDraft("");
            router.replace("/admin/payments");
          }}
        >
          Xóa lọc
        </button>
      </FilterBar>
      <DataTable
        headers={[
          "Người dùng",
          "Gói",
          "Số tiền",
          "Nguồn",
          "Trạng thái",
          "Tạo lúc",
          "Đã trả",
          "",
        ]}
        loading={loading}
        minWidth={1000}
        empty={
          !data?.items.length && (
            <EmptyState
              title="Không có thanh toán phù hợp"
              description="Thanh toán mới sẽ xuất hiện sau khi người học chọn gói."
            />
          )
        }
      >
        {data?.items.map((item) => (
          <tr key={item.id} className="hover:bg-slate-50/70">
            <td className={cellClass}>
              <Link
                href={"/admin/user?id=" + item.user_id + "&tab=payments"}
                className="font-medium text-teal-800"
              >
                {item.email}
              </Link>
            </td>
            <td className={cellClass}>{item.plan_snapshot.plan_name}</td>
            <td className={cellClass + " font-semibold text-slate-900"}>
              {fmtMoney(item.amount_vnd)}
            </td>
            <td className={cellClass}>{item.provider}</td>
            <td className={cellClass}>
              <StatusBadge status={item.status} />
            </td>
            <td className={cellClass}>{fmtDate(item.created_at)}</td>
            <td className={cellClass}>{fmtDate(item.paid_at)}</td>
            <td className={cellClass}>
              <ActionMenu
                actions={[
                  { label: "Xem chi tiết", onClick: () => setSelected(item) },
                  ...(item.status === "PENDING"
                    ? [
                        {
                          label: "Xác nhận đã nhận tiền",
                          onClick: () => setConfirming(item),
                        },
                      ]
                    : []),
                ]}
              />
            </td>
          </tr>
        ))}
      </DataTable>
      <Pagination
        page={page}
        pageSize={pageSize}
        total={data?.total || 0}
        onPage={(value) => {
          const next = new URLSearchParams(params.toString());
          next.set("page", String(value));
          router.replace("/admin/payments?" + next.toString());
        }}
      />
      <DetailDrawer
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
        title="Chi tiết thanh toán"
      >
        {selected && <PaymentDetailContent id={selected.id} />}
      </DetailDrawer>
      <ConfirmDialog
        open={!!confirming}
        onOpenChange={(open) => {
          if (!open) setConfirming(null);
        }}
        title="Xác nhận đã nhận tiền?"
        description={
          "Chỉ xác nhận sau khi đã đối soát " +
          fmtMoney(confirming?.amount_vnd) +
          " cho " +
          (confirming?.email || "người dùng") +
          ". Thao tác này sẽ kích hoạt hoặc gia hạn VIP."
        }
        confirmLabel="Xác nhận đã thanh toán"
        onConfirm={confirmPayment}
        busy={busy}
        confirmDisabled={reference.trim().length < 3}
      >
        <label className="mt-5 block text-xs font-medium text-slate-600">
          Mã giao dịch ngân hàng
          <input
            autoFocus
            className={inputClass + " mt-1 w-full"}
            value={reference}
            onChange={(event) => setReference(event.target.value)}
            placeholder="Nhập mã đã đối soát (ít nhất 3 ký tự)"
          />
        </label>
        {reference.trim().length < 3 && (
          <p className="mt-1 text-xs text-amber-700">
            Cần mã giao dịch từ 3 ký tự trước khi xác nhận.
          </p>
        )}
      </ConfirmDialog>
    </div>
  );
}
