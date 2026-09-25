"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ReadingExam } from "@/features/reading/reading-exam";

function Content() {
  const params = useSearchParams();
  return <ReadingExam id={params.get("id") || ""} />;
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
