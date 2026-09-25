"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { SpeakingExam } from "@/features/speaking/speaking-exam";

function Content() {
  const params = useSearchParams();
  return <SpeakingExam id={params.get("id") || ""} />;
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
