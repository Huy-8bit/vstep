import { ReadingExam } from "@/features/reading/reading-exam";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ReadingExam id={id} />;
}
