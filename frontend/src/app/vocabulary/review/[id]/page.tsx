import { VocabularyReview } from "@/features/vocabulary/review";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <VocabularyReview id={id} />;
}
