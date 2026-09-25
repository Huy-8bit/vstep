"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { QuestionDetailPanel } from "@/features/admin/admin-questions";

function Content() {
  const params = useSearchParams();
  return (
    <QuestionDetailPanel
      skill={params.get("skill") || ""}
      id={params.get("id") || ""}
    />
  );
}

export default function Page() {
  return (
    <Suspense
      fallback={<div className="h-80 animate-pulse rounded-lg bg-slate-100" />}
    >
      <Content />
    </Suspense>
  );
}
