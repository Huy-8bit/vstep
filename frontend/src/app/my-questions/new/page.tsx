"use client";
import { RequireAuth } from "@/features/auth/auth-provider";
import { ImportWizard } from "@/features/library/import-wizard";
export default function Page() {
  return (
    <RequireAuth>
      <ImportWizard />
    </RequireAuth>
  );
}
