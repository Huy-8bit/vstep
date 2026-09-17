import { ReadingResult } from "@/features/reading/reading-result";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ReadingResult id={id} />;
}
