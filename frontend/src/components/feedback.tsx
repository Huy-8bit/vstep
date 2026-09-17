"use client";
import { AlertCircle, LoaderCircle } from "lucide-react";
export function Loading({ text = "Đang tải..." }: { text?: string }) {
  return (
    <div
      role="status"
      className="flex min-h-52 items-center justify-center gap-3 text-sm text-stone-500"
    >
      <LoaderCircle className="size-5 animate-spin" />
      {text}
    </div>
  );
}
export function ErrorNotice({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="my-4 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <AlertCircle className="mt-0.5 size-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
export function EmptyState({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-6 py-14 text-center">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mx-auto mb-6 mt-2 max-w-md text-sm leading-6 text-stone-500">
        {description}
      </p>
      {children}
    </div>
  );
}
