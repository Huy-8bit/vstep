import { Suspense } from "react";
import { QuestionsPanel } from "@/features/admin/admin-questions";
export default function Page() {
  return (
    <Suspense
      fallback={<div className="h-80 animate-pulse rounded-lg bg-slate-100" />}
    >
      <QuestionsPanel />
    </Suspense>
  );
}
