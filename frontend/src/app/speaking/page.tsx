"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { SpeakingHome } from "@/features/speaking/speaking-home";
import { modes, type SpeakingMode } from "@/features/speaking/types";
function Content() {
  const mode = useSearchParams().get("mode");
  return (
    <SpeakingHome
      initialMode={mode && mode in modes ? (mode as SpeakingMode) : "FULL_TEST"}
    />
  );
}
export default function Page() {
  return (
    <Suspense fallback={null}>
      <Content />
    </Suspense>
  );
}
