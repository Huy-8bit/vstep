import { Suspense } from "react";
import { PaymentsPanel } from "@/features/admin/admin-commerce";
export default function Page() {
  return (
    <Suspense
      fallback={<div className="h-80 animate-pulse rounded-lg bg-slate-100" />}
    >
      <PaymentsPanel />
    </Suspense>
  );
}
