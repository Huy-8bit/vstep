"use client";
import { AlertCircle, LoaderCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

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

/** A skeleton that echoes the shape of a card grid — use instead of a spinner where layout is known. */
export function CardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-5 md:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="panel space-y-4 p-6">
          <Skeleton className="size-11 rounded-xl" />
          <Skeleton className="h-5 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
        </div>
      ))}
    </div>
  );
}

export function ErrorNotice({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="my-4 flex flex-wrap items-start justify-between gap-3 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <span className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 size-4 shrink-0" />
        {message}
      </span>
      {retry && (
        <Button size="sm" variant="outline" onClick={retry} className="border-red-200 text-red-700 hover:bg-red-100">
          Thử lại
        </Button>
      )}
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
    <div className="animate-fade-in rounded-2xl border border-dashed border-stone-300 bg-white px-6 py-14 text-center">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mx-auto mb-6 mt-2 max-w-md text-sm leading-6 text-stone-500">
        {description}
      </p>
      {children}
    </div>
  );
}
