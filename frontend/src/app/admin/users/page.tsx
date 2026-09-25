import { Suspense } from "react";
import { UsersPanel } from "@/features/admin/admin-users";
export default function Page() {
  return (
    <Suspense
      fallback={<div className="h-80 animate-pulse rounded-lg bg-slate-100" />}
    >
      <UsersPanel />
    </Suspense>
  );
}
