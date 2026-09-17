import { SpeakingHome } from "@/features/speaking/speaking-home";
import { modes, type SpeakingMode } from "@/features/speaking/types";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string }>;
}) {
  const { mode } = await searchParams;
  return (
    <SpeakingHome
      initialMode={mode && mode in modes ? (mode as SpeakingMode) : "FULL_TEST"}
    />
  );
}
