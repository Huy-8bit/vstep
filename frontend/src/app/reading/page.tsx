import { ReadingHome } from "@/features/reading/reading-home";
import {
  modes,
  questionTypes,
  type ReadingMode,
} from "@/features/reading/types";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string; type?: string }>;
}) {
  const p = await searchParams;
  return (
    <ReadingHome
      initialMode={
        p.mode && p.mode in modes ? (p.mode as ReadingMode) : "FULL_TEST"
      }
      initialType={p.type && p.type in questionTypes ? p.type : "inference"}
    />
  );
}
