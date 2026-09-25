"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ReadingHome } from "@/features/reading/reading-home";
import {
  modes,
  questionTypes,
  type ReadingMode,
} from "@/features/reading/types";
function Content() {
  const params = useSearchParams();
  const mode = params.get("mode");
  const type = params.get("type");
  return (
    <ReadingHome
      initialMode={mode && mode in modes ? (mode as ReadingMode) : "FULL_TEST"}
      initialType={type && type in questionTypes ? type : "inference"}
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
