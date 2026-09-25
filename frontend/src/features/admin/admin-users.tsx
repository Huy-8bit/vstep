"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import { Copy, Plus, X } from "lucide-react";
import { api, post } from "@/services/api";
import {
  ActionMenu,
  ConfirmDialog,
  DataTable,
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
  dangerClass,
  fmtDate,
  fmtMoney,
  fmtNumber,
  fmtRemaining,
  fmtUsd,
  inputClass,
  primaryClass,
  secondaryClass,
  useAdminData,
  type ListResponse,
} from "./admin-ui";

type Plan = {
  code: string;
  name: string;
  price_vnd: number;
  duration_days: number;
};
type User = {
  id: string;
  email: string;
  name: string | null;
  role: string;
  status: string;
  is_test_account: boolean;
  registered_at: string;
  last_active: string | null;
  trial_used: Record<string, number>;
  access: { tier: string };
  vip_start: string | null;
  vip_expiry: string | null;
  plan: Plan | null;
  total_attempts: number;
  attempts: Record<string, number>;
  total_ai_cost_usd: number | null;
};
type Payment = {
  id: string;
  plan_snapshot: { plan_name?: string };
  amount_vnd: number;
  created_at: string;
  paid_at: string | null;
  status: string;
};
type Entitlement = {
  id: string;
  plan_id: string | null;
  source: string;
  status: string;
  starts_at: string;
  expires_at: string;
};
type Detail = User & {
  entitlements: Entitlement[];
  payments: Payment[];
  learning_activity_count: number;
  server_now: string;
};

function TestUserDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}) {
  const [email, setEmail] = useState(""),
    [name, setName] = useState(""),
    [password, setPassword] = useState(""),
    [days, setDays] = useState(7);
  const [created, setCreated] = useState<{
    email: string;
    password: string | null;
  } | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit() {
    setBusy(true);
    setError("");
    try {
      const result = await post<{ generated_password: string | null }>(
        "/admin/users/test-vip",
        {
          email,
          name: name || null,
          password: password || null,
          duration_days: days,
        },
      );
      setCreated({ email, password: result.generated_password });
      onCreated();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Dialog.Root
      open={open}
      onOpenChange={(value) => {
        onOpenChange(value);
        if (!value) {
          setCreated(null);
          setEmail("");
          setName("");
          setPassword("");
          setDays(7);
          setError("");
        }
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(92vw,500px)] -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-6 shadow-2xl">
          <div className="flex items-start justify-between">
            <Dialog.Title className="text-lg font-semibold">
              Tạo tài khoản VIP thử nghiệm
            </Dialog.Title>
            <Dialog.Close
              aria-label="Đóng"
              className="rounded p-1 hover:bg-slate-100"
            >
              <X size={17} />
            </Dialog.Close>
          </div>
          <Dialog.Description className="mt-1 text-sm text-slate-500">
            Tài khoản được đánh dấu TEST và không tính vào chỉ số kinh doanh.
          </Dialog.Description>
          <div className="mt-5 space-y-3">
            <label className="block text-xs font-medium text-slate-600">
              Email
              <input
                type="email"
                className={inputClass + " mt-1 w-full"}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label className="block text-xs font-medium text-slate-600">
              Tên (tùy chọn)
              <input
                className={inputClass + " mt-1 w-full"}
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>
            <label className="block text-xs font-medium text-slate-600">
              Mật khẩu (để trống để tạo tự động)
              <input
                type="password"
                className={inputClass + " mt-1 w-full"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <label className="block text-xs font-medium text-slate-600">
              VIP trong
              <select
                className={inputClass + " mt-1 w-full"}
                value={days}
                onChange={(event) => setDays(Number(event.target.value))}
              >
                {[3, 7, 30].map((value) => (
                  <option key={value} value={value}>
                    {value} ngày
                  </option>
                ))}
              </select>
            </label>
          </div>
          {error && (
            <div className="mt-3">
              <ErrorState message={error} />
            </div>
          )}
          {created && (
            <div className="mt-4 rounded-lg border border-teal-200 bg-teal-50 p-3 text-sm">
              <p className="font-semibold text-teal-900">
                Đã tạo tài khoản. Lưu thông tin đăng nhập ngay.
              </p>
              <div className="mt-2 flex items-center justify-between gap-2">
                <span className="truncate">{created.email}</span>
                <button
                  aria-label="Sao chép email"
                  onClick={() => navigator.clipboard.writeText(created.email)}
                >
                  <Copy size={15} />
                </button>
              </div>
              {created.password && (
                <div className="mt-2 flex items-center justify-between gap-2">
                  <code className="truncate">{created.password}</code>
                  <button
                    aria-label="Sao chép mật khẩu"
                    onClick={() =>
                      navigator.clipboard.writeText(created.password || "")
                    }
                  >
                    <Copy size={15} />
                  </button>
                </div>
              )}
            </div>
          )}
          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close className={secondaryClass}>
              {created ? "Đóng" : "Hủy"}
            </Dialog.Close>
            {!created && (
              <button
                className={primaryClass}
                disabled={
                  busy ||
                  !email.includes("@") ||
                  (!!password && password.length < 8)
                }
                onClick={submit}
              >
                {busy ? "Đang tạo..." : "Tạo tài khoản"}
              </button>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function UsersPanel() {
  const router = useRouter(),
    params = useSearchParams();
  const page = Math.max(1, Number(params.get("page") || 1)),
    pageSize = 25;
  const search = params.get("search") || "";
  const [draft, setDraft] = useState(search),
    [testOpen, setTestOpen] = useState(false),
    [notice, setNotice] = useState("");
  const [confirmUser, setConfirmUser] = useState<User | null>(null),
    [busy, setBusy] = useState(false);
  function update(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value && value !== "all") next.set(key, value);
    else next.delete(key);
    next.delete("page");
    router.replace("/admin/users?" + next.toString());
  }
  const path =
    "/admin/users?" +
    new URLSearchParams({
      search,
      status: params.get("status") || "all",
      access: params.get("access") || "all",
      plan: params.get("plan") || "all",
      test: params.get("test") || "all",
      sort: params.get("sort") || "registered_desc",
      registered_after: params.get("registered_after") || "",
      last_active_after: params.get("last_active_after") || "",
      offset: String((page - 1) * pageSize),
      limit: String(pageSize),
    }).toString();
  const { data, error, setError, loading, reload } =
    useAdminData<ListResponse<User>>(path);
  const plans = useAdminData<{ items: Plan[] }>("/admin/plans");
  async function toggleStatus() {
    if (!confirmUser) return;
    setBusy(true);
    try {
      await api("/admin/users/" + confirmUser.id + "/status", {
        method: "PATCH",
        body: JSON.stringify({
          status: confirmUser.status === "ACTIVE" ? "DISABLED" : "ACTIVE",
        }),
      });
      setNotice(
        confirmUser.status === "ACTIVE"
          ? "Đã khóa tài khoản."
          : "Đã mở lại tài khoản.",
      );
      setConfirmUser(null);
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div>
      <PageHeader
        title="Người dùng"
        description="Tìm tài khoản, kiểm tra trạng thái và quản lý quyền truy cập."
        action={
          <button className={primaryClass} onClick={() => setTestOpen(true)}>
            <Plus size={15} /> Tạo tài khoản thử
          </button>
        }
      />
      <Notice text={notice} onClose={() => setNotice("")} />
      <ErrorState message={error} retry={reload} />
      <FilterBar>
        <form
          className="flex min-w-56 flex-[2] gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            update("search", draft.trim());
          }}
        >
          <SearchInput
            value={draft}
            onChange={setDraft}
            placeholder="Tên hoặc email"
          />
          <button className={secondaryClass}>Tìm</button>
        </form>
        <select
          aria-label="Trạng thái"
          className={inputClass}
          value={params.get("status") || "all"}
          onChange={(event) => update("status", event.target.value)}
        >
          <option value="all">Mọi trạng thái</option>
          <option value="ACTIVE">Hoạt động</option>
          <option value="DISABLED">Đã khóa</option>
        </select>
        <select
          aria-label="Quyền truy cập"
          className={inputClass}
          value={params.get("access") || "all"}
          onChange={(event) => update("access", event.target.value)}
        >
          <option value="all">Mọi quyền</option>
          <option value="VIP">VIP</option>
          <option value="FREE">Miễn phí</option>
        </select>
        <select
          aria-label="Gói VIP"
          className={inputClass}
          value={params.get("plan") || "all"}
          onChange={(event) => update("plan", event.target.value)}
        >
          <option value="all">Mọi gói</option>
          {plans.data?.items.map((plan) => (
            <option key={plan.code} value={plan.code}>
              {plan.name}
            </option>
          ))}
        </select>
        <select
          aria-label="Tài khoản thử nghiệm"
          className={inputClass}
          value={params.get("test") || "all"}
          onChange={(event) => update("test", event.target.value)}
        >
          <option value="all">Thật và thử</option>
          <option value="yes">Tài khoản thử</option>
          <option value="no">Tài khoản thật</option>
        </select>
        <select
          aria-label="Sắp xếp"
          className={inputClass}
          value={params.get("sort") || "registered_desc"}
          onChange={(event) => update("sort", event.target.value)}
        >
          <option value="registered_desc">Mới đăng ký</option>
          <option value="registered_asc">Cũ nhất</option>
          <option value="last_active_desc">Hoạt động gần đây</option>
          <option value="ai_cost_desc">Chi phí AI cao</option>
        </select>
        <label className="text-xs text-slate-500">
          Đăng ký từ{" "}
          <input
            type="date"
            className={inputClass + " ml-1"}
            value={(params.get("registered_after") || "").slice(0, 10)}
            onChange={(event) =>
              update(
                "registered_after",
                event.target.value
                  ? event.target.value + "T00:00:00+07:00"
                  : "",
              )
            }
          />
        </label>
        <label className="text-xs text-slate-500">
          Hoạt động từ{" "}
          <input
            type="date"
            className={inputClass + " ml-1"}
            value={(params.get("last_active_after") || "").slice(0, 10)}
            onChange={(event) =>
              update(
                "last_active_after",
                event.target.value
                  ? event.target.value + "T00:00:00+07:00"
                  : "",
              )
            }
          />
        </label>
        <button
          className={secondaryClass}
          onClick={() => {
            setDraft("");
            router.replace("/admin/users");
          }}
        >
          Xóa lọc
        </button>
      </FilterBar>
      <DataTable
        headers={[
          "Người dùng",
          "Trạng thái",
          "Quyền",
          "Gói / hạn",
          "Đăng ký",
          "Hoạt động",
          "Bài luyện",
          "",
        ]}
        loading={loading}
        empty={
          !data?.items.length && (
            <EmptyState
              title="Không có người dùng phù hợp"
              description="Thử đổi từ khóa hoặc xóa bộ lọc."
            />
          )
        }
        minWidth={1000}
      >
        {data?.items.map((user) => (
          <tr key={user.id} className="hover:bg-slate-50/70">
            <td className={cellClass}>
              <Link
                href={"/admin/user?id=" + user.id}
                className="flex min-w-48 items-center gap-3"
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                  {(user.name || user.email).slice(0, 2).toUpperCase()}
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-medium text-slate-900">
                    {user.name || user.email.split("@")[0]}
                  </span>
                  <span className="block truncate text-xs text-slate-500">
                    {user.email}
                  </span>
                </span>
              </Link>
            </td>
            <td className={cellClass}>
              <div className="flex flex-wrap gap-1">
                <StatusBadge status={user.status} />
                {user.is_test_account && <StatusBadge status="TEST" />}
                {user.role === "ADMIN" && <StatusBadge status="ADMIN" />}
              </div>
            </td>
            <td className={cellClass}>
              <StatusBadge status={user.access.tier} />
            </td>
            <td className={cellClass}>
              <span>{user.plan?.name || "—"}</span>
              <span className="block text-xs text-slate-500">
                {fmtDate(user.vip_expiry)}
              </span>
            </td>
            <td className={cellClass}>{fmtDate(user.registered_at)}</td>
            <td className={cellClass}>{fmtDate(user.last_active)}</td>
            <td className={cellClass}>{fmtNumber(user.total_attempts)}</td>
            <td className={cellClass}>
              <ActionMenu
                actions={[
                  {
                    label: "Xem chi tiết",
                    onClick: () => router.push("/admin/user?id=" + user.id),
                  },
                  {
                    label:
                      user.access.tier === "VIP" ? "Gia hạn VIP" : "Cấp VIP",
                    onClick: () =>
                      router.push(
                        "/admin/user?id=" + user.id + "&tab=subscription&grant=1",
                      ),
                  },
                  {
                    label:
                      user.status === "ACTIVE"
                        ? "Khóa tài khoản"
                        : "Mở tài khoản",
                    onClick: () => setConfirmUser(user),
                    danger: user.status === "ACTIVE",
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
        onPage={(value) => {
          const next = new URLSearchParams(params.toString());
          next.set("page", String(value));
          router.replace("/admin/users?" + next.toString());
        }}
      />
      <TestUserDialog
        open={testOpen}
        onOpenChange={setTestOpen}
        onCreated={() => {
          setNotice("Đã tạo tài khoản VIP thử nghiệm.");
          reload();
        }}
      />
      <ConfirmDialog
        open={!!confirmUser}
        onOpenChange={(open) => {
          if (!open) setConfirmUser(null);
        }}
        title={
          confirmUser?.status === "ACTIVE"
            ? "Khóa tài khoản?"
            : "Mở lại tài khoản?"
        }
        description={
          confirmUser?.status === "ACTIVE"
            ? "Người dùng sẽ không thể đăng nhập hoặc tiếp tục phiên hiện có. Lịch sử của họ được giữ lại."
            : "Người dùng có thể đăng nhập lại và sử dụng quyền còn hiệu lực."
        }
        confirmLabel={
          confirmUser?.status === "ACTIVE" ? "Khóa tài khoản" : "Mở tài khoản"
        }
        onConfirm={toggleStatus}
        busy={busy}
        danger={confirmUser?.status === "ACTIVE"}
      />
    </div>
  );
}

export function UserDetailPanel({ id }: { id: string }) {
  const router = useRouter(),
    params = useSearchParams();
  const tab = params.get("tab") || "overview";
  const { data, error, setError, loading, reload } = useAdminData<Detail>(
    "/admin/users/" + id,
  );
  const plans = useAdminData<{ items: Plan[] }>("/admin/plans");
  const [grantOpen, setGrantOpen] = useState(params.get("grant") === "1"),
    [confirmAction, setConfirmAction] = useState<"revoke" | "disable" | null>(
      null,
    ),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const [days, setDays] = useState(7),
    [reason, setReason] = useState(""),
    [plan, setPlan] = useState("VIP_7_DAYS");
  const inFlight = useRef(false);
  const expiry = data
    ? new Date(
        Math.max(
          new Date(data.server_now).getTime(),
          data.vip_expiry ? new Date(data.vip_expiry).getTime() : 0,
        ) +
          days * 86400000,
      ).toISOString()
    : "";
  function setTab(value: string) {
    const next = new URLSearchParams(params.toString());
    next.set("tab", value);
    next.set("id", id);
    next.delete("grant");
    router.replace("/admin/user?" + next.toString());
  }
  async function run(path: string, body: object, success: string) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    try {
      await post(path, body);
      setNotice(success);
      setGrantOpen(false);
      setConfirmAction(null);
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
      inFlight.current = false;
    }
  }
  async function disable() {
    if (!data) return;
    setBusy(true);
    try {
      await api("/admin/users/" + id + "/status", {
        method: "PATCH",
        body: JSON.stringify({
          status: data.status === "ACTIVE" ? "DISABLED" : "ACTIVE",
        }),
      });
      setNotice(
        data.status === "ACTIVE" ? "Đã khóa tài khoản." : "Đã mở tài khoản.",
      );
      setConfirmAction(null);
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function markTest() {
    if (!data) return;
    try {
      await api("/admin/users/" + id + "/test-account", {
        method: "PATCH",
        body: JSON.stringify({ is_test_account: !data.is_test_account }),
      });
      setNotice("Đã cập nhật tài khoản thử nghiệm.");
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    }
  }
  return (
    <div>
      <PageHeader
        title={data?.name || data?.email || "Người dùng"}
        description={data?.email}
        breadcrumb={
          <>
            <Link href="/admin/users" className="hover:text-teal-800">
              Người dùng
            </Link>
            <span className="mx-2">/</span>Chi tiết
          </>
        }
        action={
          data && (
            <div className="flex gap-2">
              <button
                className={secondaryClass}
                onClick={() => setConfirmAction("disable")}
              >
                {data.status === "ACTIVE" ? "Khóa tài khoản" : "Mở tài khoản"}
              </button>
              <button
                className={primaryClass}
                onClick={() => setGrantOpen(true)}
              >
                {data.access.tier === "VIP" ? "Gia hạn VIP" : "Cấp VIP"}
              </button>
            </div>
          )
        }
      />
      <Notice text={notice} onClose={() => setNotice("")} />
      <ErrorState message={error} retry={reload} />
      {loading && !data ? (
        <div className="h-80 animate-pulse rounded-lg bg-slate-100" />
      ) : (
        data && (
          <>
            <div className="mb-5 flex flex-wrap items-center gap-2">
              <StatusBadge status={data.status} />
              <StatusBadge status={data.access.tier} />
              {data.is_test_account && <StatusBadge status="TEST" />}
              {data.role === "ADMIN" && <StatusBadge status="ADMIN" />}
              <span className="ml-2 text-xs text-slate-500">
                Đăng ký {fmtDate(data.registered_at)} · hoạt động{" "}
                {fmtDate(data.last_active)}
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Bài luyện"
                value={fmtNumber(data.total_attempts)}
              />
              <MetricCard
                label="Chi phí AI"
                value={fmtUsd(data.total_ai_cost_usd)}
              />
              <MetricCard label="Thanh toán" value={data.payments.length} />
              <MetricCard
                label="Gói hiện tại"
                value={data.plan?.name || data.access.tier}
              />
            </div>
            <nav
              className="my-6 flex gap-1 overflow-x-auto border-b border-slate-200"
              aria-label="Chi tiết người dùng"
            >
              {[
                ["overview", "Tổng quan"],
                ["subscription", "VIP"],
                ["payments", "Thanh toán"],
                ["practice", "Luyện tập"],
                ["ai", "AI"],
                ["learning", "Học tập"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  aria-current={tab === key ? "page" : undefined}
                  className={
                    "whitespace-nowrap border-b-2 px-4 py-2.5 text-sm " +
                    (tab === key
                      ? "border-teal-700 font-semibold text-teal-800"
                      : "border-transparent text-slate-500 hover:text-slate-900")
                  }
                >
                  {label}
                </button>
              ))}
            </nav>
            {tab === "overview" && (
              <div className="grid gap-4 lg:grid-cols-2">
                <Section title="Tài khoản">
                  <dl className="grid grid-cols-2 gap-4 p-5 text-sm">
                    <div>
                      <dt className="text-slate-500">Email</dt>
                      <dd className="mt-1 font-medium">{data.email}</dd>
                    </div>
                    <div>
                      <dt className="text-slate-500">Vai trò</dt>
                      <dd className="mt-1">{data.role}</dd>
                    </div>
                    <div>
                      <dt className="text-slate-500">Đăng ký</dt>
                      <dd className="mt-1">{fmtDate(data.registered_at)}</dd>
                    </div>
                    <div>
                      <dt className="text-slate-500">Đăng nhập gần nhất</dt>
                      <dd className="mt-1">{fmtDate(data.last_active)}</dd>
                    </div>
                  </dl>
                  <div className="border-t px-5 py-4">
                    <button className={secondaryClass} onClick={markTest}>
                      {data.is_test_account
                        ? "Bỏ nhãn thử nghiệm"
                        : "Đánh dấu thử nghiệm"}
                    </button>
                  </div>
                </Section>
                <Section title="Quyền truy cập">
                  <div className="space-y-3 p-5 text-sm">
                    <p>
                      <StatusBadge status={data.access.tier} />{" "}
                      <span className="ml-2">
                        {data.plan?.name || "Không có gói trả phí"}
                      </span>
                    </p>
                    <p>
                      Hiệu lực: {fmtDate(data.vip_start)} →{" "}
                      {fmtDate(data.vip_expiry)}
                    </p>
                    <p>
                      Trial đã dùng: Writing{" "}
                      {data.trial_used.WRITING_TASK1 || 0}, Speaking{" "}
                      {data.trial_used.SPEAKING_PART1 || 0}
                    </p>
                  </div>
                </Section>
              </div>
            )}
            {tab === "subscription" && (
              <div className="space-y-4">
                <Section
                  title="Quyền hiện tại"
                  action={
                    <button
                      className={dangerClass}
                      onClick={() => setConfirmAction("revoke")}
                      disabled={data.access.tier !== "VIP"}
                    >
                      Thu hồi VIP
                    </button>
                  }
                >
                  <div className="grid gap-4 p-5 text-sm sm:grid-cols-4">
                    <div>
                      <p className="text-slate-500">Gói</p>
                      <strong>
                        {data.plan?.name || "Cấp thủ công / Không có"}
                      </strong>
                    </div>
                    <div>
                      <p className="text-slate-500">Bắt đầu</p>
                      {fmtDate(data.vip_start)}
                    </div>
                    <div>
                      <p className="text-slate-500">Hết hạn</p>
                      {fmtDate(data.vip_expiry)}
                    </div>
                    <div>
                      <p className="text-slate-500">Còn lại</p>
                      {data.vip_expiry
                        ? fmtRemaining(
                            (new Date(data.vip_expiry).getTime() -
                              new Date(data.server_now).getTime()) /
                              1000,
                          )
                        : "—"}
                    </div>
                  </div>
                </Section>
                <Section title="Lịch sử VIP">
                  <DataTable
                    headers={["Nguồn", "Bắt đầu", "Hết hạn", "Trạng thái"]}
                    empty={
                      !data.entitlements.length && (
                        <EmptyState
                          title="Chưa có gói VIP"
                          description="Cấp hoặc đối soát thanh toán để kích hoạt VIP."
                        />
                      )
                    }
                  >
                    {data.entitlements.map((item) => (
                      <tr key={item.id}>
                        <td className={cellClass}>
                          <StatusBadge status={item.source} />
                        </td>
                        <td className={cellClass}>{fmtDate(item.starts_at)}</td>
                        <td className={cellClass}>
                          {fmtDate(item.expires_at)}
                        </td>
                        <td className={cellClass}>
                          <StatusBadge status={item.status} />
                        </td>
                      </tr>
                    ))}
                  </DataTable>
                </Section>
                <Section title="Tạo thanh toán thủ công">
                  <div className="flex flex-wrap items-end gap-2 p-5">
                    <label className="text-xs text-slate-500">
                      Chọn gói
                      <select
                        className={inputClass + " mt-1 block"}
                        value={plan}
                        onChange={(event) => setPlan(event.target.value)}
                      >
                        {plans.data?.items.map((item) => (
                          <option key={item.code} value={item.code}>
                            {item.name} · {fmtMoney(item.price_vnd)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      disabled={busy}
                      className={secondaryClass}
                      onClick={() =>
                        run(
                          "/admin/users/" + id + "/manual-payment",
                          { plan_code: plan },
                          "Đã tạo khoản chờ. Hãy đối soát ở mục Thanh toán.",
                        )
                      }
                    >
                      Tạo khoản chờ
                    </button>
                    <p className="w-full text-xs text-slate-500">
                      Tạo khoản chờ không kích hoạt VIP.
                    </p>
                  </div>
                </Section>
              </div>
            )}
            {tab === "payments" && (
              <DataTable
                headers={[
                  "Gói",
                  "Số tiền",
                  "Tạo lúc",
                  "Thanh toán lúc",
                  "Trạng thái",
                ]}
                empty={
                  !data.payments.length && (
                    <EmptyState
                      title="Chưa có thanh toán"
                      description="Lịch sử thanh toán của người dùng sẽ xuất hiện tại đây."
                    />
                  )
                }
              >
                {data.payments.map((item) => (
                  <tr key={item.id}>
                    <td className={cellClass}>
                      {item.plan_snapshot.plan_name || "VIP"}
                    </td>
                    <td className={cellClass}>{fmtMoney(item.amount_vnd)}</td>
                    <td className={cellClass}>{fmtDate(item.created_at)}</td>
                    <td className={cellClass}>{fmtDate(item.paid_at)}</td>
                    <td className={cellClass}>
                      <StatusBadge status={item.status} />
                    </td>
                  </tr>
                ))}
              </DataTable>
            )}
            {tab === "practice" && (
              <div className="grid gap-3 sm:grid-cols-3">
                {[
                  ["Writing", data.attempts.writing],
                  ["Speaking", data.attempts.speaking],
                  ["Reading", data.attempts.reading],
                ].map(([label, value]) => (
                  <MetricCard
                    key={label}
                    label={String(label)}
                    value={fmtNumber(Number(value))}
                  />
                ))}
              </div>
            )}
            {tab === "ai" && (
              <Section title="Chi phí AI của tài khoản">
                <div className="p-5">
                  <p className="text-2xl font-semibold">
                    {fmtUsd(data.total_ai_cost_usd)}
                  </p>
                  <p className="mt-2 text-xs text-slate-500">
                    Chi phí ước tính; lượt chưa có đơn giá không được coi là
                    miễn phí.
                  </p>
                </div>
              </Section>
            )}
            {tab === "learning" && (
              <Section title="Hoạt động học tập">
                <div className="p-5">
                  <p className="text-2xl font-semibold">
                    {fmtNumber(data.learning_activity_count)}
                  </p>
                  <p className="mt-2 text-xs text-slate-500">
                    Sự kiện sản phẩm đã ghi nhận.
                  </p>
                </div>
              </Section>
            )}
          </>
        )
      )}
      <Dialog.Root open={grantOpen} onOpenChange={setGrantOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/40" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(92vw,500px)] -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <Dialog.Title className="text-lg font-semibold">
                {data?.access.tier === "VIP" ? "Gia hạn VIP" : "Cấp VIP"}
              </Dialog.Title>
              <Dialog.Close aria-label="Đóng">
                <X size={17} />
              </Dialog.Close>
            </div>
            <Dialog.Description className="mt-1 text-sm text-slate-500">
              {data?.email}
            </Dialog.Description>
            <div className="mt-5 space-y-4">
              <div>
                <p className="mb-2 text-xs font-medium text-slate-600">
                  Thời hạn
                </p>
                <div className="flex flex-wrap gap-2">
                  {[3, 7, 30].map((value) => (
                    <button
                      key={value}
                      aria-pressed={days === value}
                      className={days === value ? primaryClass : secondaryClass}
                      onClick={() => setDays(value)}
                    >
                      {plans.data?.items.find(
                        (item) => item.duration_days === value,
                      )?.name || value + " ngày"}
                      {plans.data?.items.find(
                        (item) => item.duration_days === value,
                      )?.price_vnd != null &&
                        " · " +
                          fmtMoney(
                            plans.data.items.find(
                              (item) => item.duration_days === value,
                            )?.price_vnd,
                          )}
                    </button>
                  ))}
                  <input
                    type="number"
                    min={1}
                    max={365}
                    aria-label="Số ngày tùy chỉnh"
                    className={inputClass + " w-28"}
                    value={days}
                    onChange={(event) => setDays(Number(event.target.value))}
                  />
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Cấp thủ công không tạo giao dịch và không tính doanh thu.
                </p>
              </div>
              <label className="block text-xs font-medium text-slate-600">
                Lý do cấp/gia hạn
                <input
                  className={inputClass + " mt-1 w-full"}
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  placeholder="Ví dụ: Hỗ trợ người dùng"
                />
              </label>
              <div className="rounded-lg bg-slate-50 p-3 text-sm">
                <p>
                  Hạn hiện tại: <strong>{fmtDate(data?.vip_expiry)}</strong>
                </p>
                <p className="mt-1">
                  Hạn sau khi cấp:{" "}
                  <strong className="text-teal-800">{fmtDate(expiry)}</strong>
                </p>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Dialog.Close className={secondaryClass}>Hủy</Dialog.Close>
              <button
                className={primaryClass}
                disabled={busy || days < 1 || days > 365}
                onClick={() =>
                  run(
                    "/admin/users/" + id + "/grant-vip",
                    {
                      duration_days: days,
                      reason: reason.trim() || "Cấp VIP thủ công",
                    },
                    "Đã cấp hoặc gia hạn VIP.",
                  )
                }
              >
                {busy ? "Đang xử lý..." : "Xác nhận cấp VIP"}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
      <ConfirmDialog
        open={!!confirmAction}
        onOpenChange={(open) => {
          if (!open) setConfirmAction(null);
        }}
        title={
          confirmAction === "revoke"
            ? "Thu hồi VIP?"
            : data?.status === "ACTIVE"
              ? "Khóa tài khoản?"
              : "Mở lại tài khoản?"
        }
        description={
          confirmAction === "revoke"
            ? "Quyền VIP còn hiệu lực sẽ bị thu hồi ngay. Lịch sử và bài làm vẫn được giữ lại."
            : data?.status === "ACTIVE"
              ? "Người dùng sẽ không thể đăng nhập. Dữ liệu học tập vẫn được giữ."
              : "Người dùng có thể đăng nhập lại."
        }
        confirmLabel={
          confirmAction === "revoke"
            ? "Thu hồi VIP"
            : data?.status === "ACTIVE"
              ? "Khóa tài khoản"
              : "Mở tài khoản"
        }
        onConfirm={() => {
          if (confirmAction === "revoke")
            run(
              "/admin/users/" + id + "/revoke-vip",
              { reason: reason.trim() || "Admin thu hồi quyền VIP" },
              "Đã thu hồi VIP.",
            );
          else void disable();
        }}
        busy={busy}
        danger={confirmAction === "revoke" || data?.status === "ACTIVE"}
      />
    </div>
  );
}
