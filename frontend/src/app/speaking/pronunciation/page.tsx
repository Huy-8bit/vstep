import { Suspense } from "react";
import { PronunciationCoach } from "@/features/speaking/pronunciation-coach";
import { Loading } from "@/components/feedback";
export default function Page() {
  return (
    <Suspense fallback={<Loading />}>
      <PronunciationCoach />
    </Suspense>
  );
}
