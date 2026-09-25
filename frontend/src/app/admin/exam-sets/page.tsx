import { Suspense } from "react";
import { ExamSetsPanel } from "@/features/admin/admin-exam-sets";
export default function Page() {
  return (
    <Suspense>
      <ExamSetsPanel />
    </Suspense>
  );
}
