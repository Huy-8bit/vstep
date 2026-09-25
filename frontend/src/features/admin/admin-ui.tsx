"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  Search,
  X,
} from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import { api } from "@/services/api";

export type ListResponse<T> = { items: T[]; total: number };
export const fmtNumber = (value: number | null | undefined) =>
  new Intl.NumberFormat("vi-VN").format(value ?? 0);
export const fmtMoney = (value: number | null | undefined) =>
  fmtNumber(value) + "đ";
export const fmtUsd = (value: number | null | undefined) =>
  value == null ? "Chưa rõ" : "$" + value.toFixed(4);
export const fmtDate = (value: string | null | undefined) =>
  value
    ? new Intl.DateTimeFormat("vi-VN", {
        dateStyle: "short",
        timeStyle: "short",
        timeZone: "Asia/Ho_Chi_Minh",
      }).format(new Date(value))
    : "—";
export function fmtRemaining(seconds: number) {
  if (seconds <= 0) return "Đã hết hạn";
  const hours = Math.ceil(seconds / 3600);
  return hours < 24
    ? hours + " giờ"
    : Math.floor(hours / 24) + " ngày " + (hours % 24) + " giờ";
}
export const inputClass =
  "h-9 min-w-0 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-600/15 disabled:bg-slate-50 disabled:text-slate-400";
export const primaryClass =
  "inline-flex h-9 items-center justify-center gap-2 rounded-md bg-teal-800 px-3.5 text-sm font-semibold text-white transition hover:bg-teal-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 disabled:cursor-not-allowed disabled:opacity-50";
export const secondaryClass =
  "inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 disabled:opacity-50";
export const dangerClass =
  "inline-flex h-9 items-center justify-center gap-2 rounded-md border border-rose-200 bg-white px-3.5 text-sm font-medium text-rose-700 transition hover:bg-rose-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-700 disabled:opacity-50";
export const cellClass =
  "border-b border-slate-100 px-4 py-3 align-middle text-sm text-slate-700";

export function useAdminData<T>(path: string) {
  const [result, setResult] = useState<{
    key: string;
    data: T | null;
    error: string;
  }>({
    key: "",
    data: null,
    error: "",
  });
  const [version, setVersion] = useState(0);
  const key = path + ":" + version;
  const reload = useCallback(() => setVersion((value) => value + 1), []);
  useEffect(() => {
    let active = true;
    api<T>(path)
      .then((data) => {
        if (active) setResult({ key, data, error: "" });
      })
      .catch((failure) => {
        if (active)
          setResult({ key, data: null, error: (failure as Error).message });
      });
    return () => {
      active = false;
    };
  }, [path, key]);
  const current = result.key === key;
  const setError = (message: string) =>
    setResult((previous) => ({
      key,
      data: current ? previous.data : null,
      error: message,
    }));
  const data = current ? result.data : null;
  const error = current ? result.error : "";
  const loading = !current;
  return { data, error, setError, loading, reload };
}

export function PageHeader({
  title,
  description,
  action,
  breadcrumb,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  breadcrumb?: ReactNode;
}) {
  return (
    <header className="mb-6">
      {breadcrumb && (
        <div className="mb-4 text-xs text-slate-500">{breadcrumb}</div>
      )}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[25px] font-semibold tracking-tight text-slate-950">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-sm text-slate-500">{description}</p>
          )}
        </div>
        {action}
      </div>
    </header>
  );
}
export function Section({
  title,
  action,
  children,
  className = "",
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={"rounded-lg border border-slate-200 bg-white " + className}
    >
      {(title || action) && (
        <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-3.5">
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
export function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-4">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-[25px] font-semibold leading-tight tracking-tight text-slate-950">
        {value}
      </p>
      {hint && <p className="mt-2 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
const statusStyles: Record<string, string> = {
  ACTIVE: "border-emerald-200 bg-emerald-50 text-emerald-800",
  VIP: "border-teal-200 bg-teal-50 text-teal-800",
  PAID: "border-emerald-200 bg-emerald-50 text-emerald-800",
  PUBLISHED: "border-emerald-200 bg-emerald-50 text-emerald-800",
  FREE: "border-slate-200 bg-slate-50 text-slate-600",
  PENDING: "border-amber-200 bg-amber-50 text-amber-800",
  DRAFT: "border-amber-200 bg-amber-50 text-amber-800",
  DISABLED: "border-rose-200 bg-rose-50 text-rose-800",
  REVOKED: "border-rose-200 bg-rose-50 text-rose-800",
  FAILED: "border-rose-200 bg-rose-50 text-rose-800",
  TEST: "border-violet-200 bg-violet-50 text-violet-800",
  ON: "border-emerald-200 bg-emerald-50 text-emerald-800",
  OFF: "border-slate-200 bg-slate-50 text-slate-600",
  ADMIN: "border-indigo-200 bg-indigo-50 text-indigo-800",
};
const statusLabels: Record<string, string> = {
  ACTIVE: "Hoạt động",
  DISABLED: "Đã khóa",
  VIP: "VIP",
  FREE: "Miễn phí",
  TEST: "Thử nghiệm",
  ADMIN: "Admin",
  ON: "Bật",
  OFF: "Tắt",
  PAID: "Đã trả",
  PENDING: "Chờ đối soát",
  DRAFT: "Bản nháp",
  PUBLISHED: "Đã xuất bản",
  IMPORTED: "Đã nhập",
  REVOKED: "Đã thu hồi",
  EXPIRED: "Hết hạn",
  INTERNAL: "Nội bộ",
  FREE_TRIAL: "Trial",
  PURCHASE: "Đã mua",
  ADMIN_GRANT: "Admin cấp",
  REFUNDED: "Đã hoàn tiền",
  CANCELLED: "Đã hủy",
  ARCHIVED: "Đã lưu trữ",
};
export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={
        "inline-flex whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-semibold " +
        (statusStyles[status] || "border-slate-200 bg-slate-50 text-slate-600")
      }
    >
      {statusLabels[status] || status}
    </span>
  );
}
export function DataTable({
  headers,
  children,
  empty,
  loading,
  minWidth = 760,
}: {
  headers: string[];
  children?: ReactNode;
  empty?: ReactNode;
  loading?: boolean;
  minWidth?: number;
}) {
  return (
    <div className="overflow-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full table-auto text-left" style={{ minWidth }}>
        <thead className="sticky top-0 z-10 bg-slate-50">
          <tr>
            {headers.map((header) => (
              <th
                key={header}
                className="border-b border-slate-200 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading
            ? Array.from({ length: 5 }, (_, index) => (
                <tr key={index}>
                  {headers.map((header) => (
                    <td key={header} className={cellClass}>
                      <div className="h-4 w-4/5 animate-pulse rounded bg-slate-100" />
                    </td>
                  ))}
                </tr>
              ))
            : children}
        </tbody>
      </table>
      {!loading && empty && (
        <div className="border-t border-slate-100">{empty}</div>
      )}
    </div>
  );
}
export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
    >
      <AlertCircle size={16} />
      <span className="flex-1">{message}</span>
      {retry && (
        <button className="font-semibold underline" onClick={retry}>
          Thử lại
        </button>
      )}
    </div>
  );
}
export function Notice({
  text,
  onClose,
}: {
  text: string;
  onClose: () => void;
}) {
  if (!text) return null;
  return (
    <div
      role="status"
      className="mb-4 flex items-center gap-3 rounded-lg border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-900"
    >
      <span className="flex-1">{text}</span>
      <button aria-label="Đóng thông báo" onClick={onClose}>
        <X size={15} />
      </button>
    </div>
  );
}
export function SearchInput({
  value,
  onChange,
  placeholder = "Tìm kiếm...",
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="relative block min-w-48 flex-1">
      <Search
        size={15}
        className="pointer-events-none absolute left-3 top-2.5 text-slate-400"
      />
      <input
        className={inputClass + " w-full pl-9"}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}
export function FilterBar({ children }: { children: ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white p-3">
      {children}
    </div>
  );
}
export function Pagination({
  page,
  pageSize,
  total,
  onPage,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex items-center justify-between gap-3 py-4 text-xs text-slate-500">
      <span>
        {total
          ? fmtNumber((page - 1) * pageSize + 1) +
            "–" +
            fmtNumber(Math.min(page * pageSize, total)) +
            " / " +
            fmtNumber(total)
          : "0 kết quả"}
      </span>
      <div className="flex items-center gap-2">
        <button
          className={secondaryClass}
          aria-label="Trang trước"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          <ChevronLeft size={15} />
        </button>
        <span>
          Trang {page}/{pages}
        </span>
        <button
          className={secondaryClass}
          aria-label="Trang sau"
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}
export function ActionMenu({
  actions,
}: {
  actions: { label: string; onClick: () => void; danger?: boolean }[];
}) {
  return (
    <details className="relative inline-block text-left">
      <summary
        className="flex size-8 list-none items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-teal-700"
        aria-label="Tác vụ"
      >
        <MoreHorizontal size={17} />
      </summary>
      <div className="absolute right-0 z-30 mt-1 min-w-40 rounded-md border border-slate-200 bg-white p-1 shadow-lg">
        {actions.map((action) => (
          <button
            key={action.label}
            className={
              "block w-full rounded px-3 py-2 text-left text-sm hover:bg-slate-50 " +
              (action.danger ? "text-rose-700" : "text-slate-700")
            }
            onClick={(event) => {
              action.onClick();
              event.currentTarget.closest("details")?.removeAttribute("open");
            }}
          >
            {action.label}
          </button>
        ))}
      </div>
    </details>
  );
}
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  onConfirm,
  busy,
  confirmDisabled,
  danger = false,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void;
  busy?: boolean;
  confirmDisabled?: boolean;
  danger?: boolean;
  children?: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(92vw,480px)] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-slate-200 bg-white p-6 shadow-2xl">
          <Dialog.Title className="text-lg font-semibold text-slate-950">
            {title}
          </Dialog.Title>
          <Dialog.Description className="mt-2 text-sm leading-6 text-slate-600">
            {description}
          </Dialog.Description>
          {children}
          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close className={secondaryClass}>Hủy</Dialog.Close>
            <button
              disabled={busy || confirmDisabled}
              className={danger ? dangerClass : primaryClass}
              onClick={onConfirm}
            >
              {busy ? "Đang xử lý..." : confirmLabel}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
export function DetailDrawer({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/35" />
        <Dialog.Content className="fixed inset-y-0 right-0 z-50 w-[min(100vw,520px)] overflow-auto border-l border-slate-200 bg-white p-6 shadow-2xl">
          <div className="flex items-start justify-between gap-3">
            <Dialog.Title className="text-xl font-semibold">
              {title}
            </Dialog.Title>
            <Dialog.Close
              aria-label="Đóng"
              className="rounded-md p-1 hover:bg-slate-100"
            >
              <X size={18} />
            </Dialog.Close>
          </div>
          <Dialog.Description className="sr-only">
            Chi tiết bản ghi quản trị
          </Dialog.Description>
          <div className="mt-6">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
